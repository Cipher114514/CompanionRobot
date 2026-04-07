"""
对话记忆系统 - 带开关控制
支持RAG的开启/关闭，方便A/B测试
"""

import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta
import json
from pathlib import Path
import hashlib

from config import RAGConfig


class ConversationalMemory:
    """对话记忆系统"""

    def __init__(self):
        if not RAGConfig.is_enabled():
            print("⚠️ RAG已禁用，记忆系统将不执行任何操作")
            self.enabled = False
            return

        self.enabled = True
        print(f"✅ RAG已启用，数据库路径: {RAGConfig.DB_PATH}")

        # 初始化向量数据库
        Path(RAGConfig.DB_PATH).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=RAGConfig.DB_PATH)
        self.collection = self.client.get_or_create_collection(
            name="conversations"
        )

        # 加载embedding模型
        print(f"📥 加载embedding模型: {RAGConfig.EMBEDDING_MODEL}")
        self.embedder = SentenceTransformer(RAGConfig.EMBEDDING_MODEL)
        print(f"✅ Embedding模型加载完成，向量维度: {self.embedder.get_sentence_embedding_dimension()}")

        # 初始化缓存
        if RAGConfig.ENABLE_CACHE:
            self.cache = {}
            print(f"✅ 缓存已启用，大小: {RAGConfig.CACHE_SIZE}")
        else:
            self.cache = None

    def is_enabled(self):
        """检查记忆系统是否启用"""
        return self.enabled

    def add_message(self, user_id, user_message, bot_response, metadata=None):
        """添加一条对话到记忆"""
        if not self.enabled:
            return

        try:
            # 准备文档内容
            document = {
                "user": user_message,
                "bot": bot_response,
                "time": datetime.now().isoformat()
            }

            # 生成向量
            text = f"用户: {user_message}\n助手: {bot_response}"
            embedding = self.embedder.encode(text).tolist()

            # 存储到向量数据库
            self.collection.add(
                documents=[json.dumps(document, ensure_ascii=False)],
                embeddings=[embedding],
                metadatas=[{
                    "user_id": str(user_id),
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }],
                ids=[f"{user_id}_{datetime.now().timestamp()}"]
            )

            if RAGConfig.VERBOSE_RETRIEVAL:
                print(f"💾 已存储对话: {user_message[:50]}...")

        except Exception as e:
            print(f"❌ 存储对话失败: {e}")

    def retrieve(self, user_id, query, top_k=None, days=None):
        """检索相关记忆"""
        if not self.enabled:
            return []

        try:
            # 使用配置默认值
            top_k = top_k or RAGConfig.RETRIEVAL_TOP_K
            days = days or RAGConfig.RETRIEVAL_DAYS

            # 检查缓存
            if self.cache:
                cache_key = self._get_cache_key(user_id, query)
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    if (datetime.now().timestamp() - cached_result['timestamp']) < RAGConfig.CACHE_TTL:
                        if RAGConfig.VERBOSE_RETRIEVAL:
                            print(f"✅ 缓存命中: {query[:50]}...")
                        return cached_result['memories']

            # 生成查询向量
            query_embedding = self.embedder.encode(query).tolist()

            # 向量搜索（简化过滤条件）
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,  # 获取更多结果以便手动过滤
                where={"user_id": str(user_id)}  # 仅按用户ID过滤
            )

            # 格式化结果并手动过滤时间
            memories = []
            if results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    data = json.loads(doc)
                    memory_time = datetime.fromisoformat(
                        results['metadatas'][0][i]['timestamp']
                    )
                    days_ago = (datetime.now() - memory_time).days

                    # 手动过滤：只保留指定天数内的记忆
                    if days_ago <= days:
                        memories.append({
                            'user_message': data['user'],
                            'bot_response': data['bot'],
                            'days_ago': days_ago,
                            'timestamp': memory_time.isoformat(),
                            'similarity': results['distances'][0][i]
                        })

                    # 达到所需数量后停止
                    if len(memories) >= top_k:
                        break

                # 存入缓存
                if self.cache:
                    self._store_in_cache(user_id, query, memories)

            if RAGConfig.VERBOSE_RETRIEVAL:
                print(f"🔍 检索到 {len(memories)} 条记忆")

            return memories

        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []

    def _get_cache_key(self, user_id, query):
        """生成缓存键"""
        content = f"{user_id}:{query}"
        return hashlib.md5(content.encode()).hexdigest()

    def _store_in_cache(self, user_id, query, memories):
        """存入缓存"""
        if not self.cache:
            return

        cache_key = self._get_cache_key(user_id, query)
        self.cache[cache_key] = {
            'memories': memories,
            'timestamp': datetime.now().timestamp()
        }

        # 清理过期缓存
        self._cleanup_cache()

    def _cleanup_cache(self):
        """清理缓存"""
        if not self.cache:
            return

        current_time = datetime.now().timestamp()

        # 删除过期缓存
        self.cache = {
            k: v for k, v in self.cache.items()
            if current_time - v['timestamp'] < RAGConfig.CACHE_TTL
        }

        # 保持缓存大小
        if len(self.cache) > RAGConfig.CACHE_SIZE:
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            self.cache = dict(sorted_items[int(len(sorted_items) * 0.2):])

    def get_stats(self, user_id):
        """获取统计信息"""
        if not self.enabled:
            return {"status": "disabled"}

        try:
            # 获取用户所有对话
            all_memories = self.collection.get(
                where={"user_id": str(user_id)}
            )

            total_count = len(all_memories['documents'])

            # 获取最近30天的对话
            time_threshold = (datetime.now() - timedelta(days=30)).isoformat()
            recent_memories = self.collection.get(
                where={
                    "user_id": str(user_id),
                    "timestamp": {"$gt": time_threshold}
                }
            )
            recent_count = len(recent_memories['documents'])

            return {
                "status": "enabled",
                "total_conversations": total_count,
                "recent_conversations_30d": recent_count,
                "cache_enabled": self.cache is not None,
                "cache_size": len(self.cache) if self.cache else 0
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def clear_user_memory(self, user_id):
        """清除用户记忆（用于测试或隐私）"""
        if not self.enabled:
            return

        try:
            # 获取用户所有记忆的ID
            all_memories = self.collection.get(
                where={"user_id": str(user_id)}
            )

            if all_memories['ids']:
                self.collection.delete(ids=all_memories['ids'])
                print(f"✅ 已清除用户 {user_id} 的 {len(all_memories['ids'])} 条记忆")

        except Exception as e:
            print(f"❌ 清除记忆失败: {e}")


# 全局实例（单例）
_memory_instance = None


def get_memory_system():
    """获取记忆系统实例（单例模式）"""
    global _memory_instance

    if _memory_instance is None:
        _memory_instance = ConversationalMemory()

    return _memory_instance


def reset_memory_system():
    """重置记忆系统（用于开关切换）"""
    global _memory_instance
    _memory_instance = None

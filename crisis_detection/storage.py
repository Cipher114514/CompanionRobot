"""危机事件存储模块"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class CrisisEvent(Base):
    """危机事件记录"""
    __tablename__ = "crisis_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)  # ← 添加索引
    level = Column(Integer, default=0, index=True)          # ← 添加索引
    confidence = Column(Float, default=0.0)
    keywords = Column(Text, default="")
    suggested_action = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now, index=True)  # ← 添加索引
    handled = Column(Integer, default=0, index=True)        # ← 添加索引
    handler_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "level": self.level,
            "confidence": self.confidence,
            "keywords": self.keywords.split(",") if self.keywords else [],
            "suggested_action": self.suggested_action,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "handled": bool(self.handled),
            "handler_id": self.handler_id,
            "notes": self.notes
        }


class CrisisStorage:
    """危机事件存储"""
    
    def __init__(self, db_url: str = "sqlite:///crisis_events.db"):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def log_event(self, result, user_id: int) -> CrisisEvent:
        """记录危机事件"""
        try:
            event = CrisisEvent(
                user_id=user_id,
                level=result.level,
                confidence=result.confidence,
                keywords=",".join(result.keywords) if result.keywords else "",
                suggested_action=result.suggested_action
            )
            self.session.add(event)
            self.session.flush()  # ← 确保 id 立即可用
            self.session.commit()
            return event
        except Exception as e:
            self.session.rollback()
            print(f"记录危机事件失败：{e}")
            raise
    
    def get_unhandled_events(self, user_id: Optional[int] = None) -> List[CrisisEvent]:
        """获取未处理事件"""
        try:
            query = self.session.query(CrisisEvent).filter_by(handled=0)
            if user_id:
                query = query.filter_by(user_id=user_id)
            return query.all()
        except Exception as e:
            print(f"查询未处理事件失败：{e}")
            return []
    
    def mark_handled(self, event_id: int, handler_id: int, notes: str = ""):
        """标记事件已处理"""
        try:
            event = self.session.query(CrisisEvent).filter_by(id=event_id).first()
            if event:
                event.handled = 1
                event.handler_id = handler_id
                event.notes = notes
                self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"标记事件失败：{e}")
    
    def close(self):
        """关闭会话"""
        self.session.close()
        self.engine.dispose()
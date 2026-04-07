// 聊天界面JavaScript
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const recordBtn = document.getElementById('recordBtn');
const audioPlayer = document.getElementById('audioPlayer');
const statusDiv = document.getElementById('status');

// 录音相关变量
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// ==================== 猜你想问 ====================

const suggestedList = document.getElementById('suggestedList');

// 更新"猜你想问"
function updateSuggestedQuestions(questions) {
    if (!questions || questions.length === 0) {
        suggestedList.innerHTML = '<span class="suggested-placeholder">继续对话后会显示相关问题...</span>';
        return;
    }

    suggestedList.innerHTML = '';
    questions.forEach(question => {
        const item = document.createElement('span');
        item.className = 'suggested-item';
        item.textContent = question;
        item.onclick = () => {
            messageInput.value = question;
            messageInput.focus();
            sendMessage();
        };
        suggestedList.appendChild(item);
    });
}

// 清空"猜你想问"
function clearSuggestedQuestions() {
    suggestedList.innerHTML = '<span class="suggested-placeholder">AI回复后会显示相关问题...</span>';
}

// ==================== AI主动关心 ====================

// 提取并显示AI的主动询问
function extractAndShowAIQuestions(botMessage) {
    // 查找消息中的问句
    const questionPatterns = [
        /[^。！？]*？/g,  // 以？结尾的句子
        /[^。！？]*最近[^。！？]*/g,  // 包含"最近"的句子
        /[^。！？]*怎么样[^。！？]*/g,  // 包含"怎么样"的句子
        /[^。！？]*吗[？]?/g,  // 包含"吗"的疑问句
    ];

    let questions = [];

    for (const pattern of questionPatterns) {
        const matches = botMessage.match(pattern);
        if (matches) {
            questions = questions.concat(matches.filter(q => q.length > 5 && q.length < 50));
        }
    }

    // 去重
    questions = [...new Set(questions)];

    if (questions.length > 0) {
        // 显示AI主动关心的问题
        showAIActiveQuestions(questions.slice(0, 3)); // 最多显示3个
    }
}

// 显示AI主动关心的问题
function showAIActiveQuestions(questions) {
    // 在"猜你想问"区域显示
    if (!suggestedList) return;

    const originalHTML = suggestedList.innerHTML;

    suggestedList.innerHTML = `
        <div class="ai-active-questions">
            <div class="ai-questions-title">💭 AI想了解：</div>
            <div class="ai-questions-list">
                ${questions.map(q => `
                    <button class="ai-question-btn" onclick="answerAIQuestion('${q.replace(/'/g, "\\'")}')')">
                        ${q}
                    </button>
                `).join('')}
            </div>
        </div>
    `;

    // 10秒后恢复原来的内容
    setTimeout(() => {
        if (suggestedList.querySelector('.ai-active-questions')) {
            suggestedList.innerHTML = originalHTML;
        }
    }, 10000);
}

// 回答AI的问题
window.answerAIQuestion = function(question) {
    messageInput.value = question;
    messageInput.focus();
    sendMessage();
}

// ==================== AI主动问候功能 ====================

const ACTIVE_GREETING_KEY = 'last_greeting_check';
const LAST_CHAT_KEY = 'last_chat_time';

// 检查是否需要主动问候
function checkActiveGreeting() {
    const now = Date.now();
    const lastChatTime = localStorage.getItem(LAST_CHAT_KEY);
    const lastGreetingCheck = localStorage.getItem(ACTIVE_GREETING_KEY);

    // 首次访问或没有聊天记录，不问候
    if (!lastChatTime) {
        localStorage.setItem(ACTIVE_GREETING_KEY, now.toString());
        return;
    }

    const daysSinceLastChat = (now - parseInt(lastChatTime)) / (1000 * 60 * 60 * 24);

    // 如果超过3天没聊天，显示主动问候
    if (daysSinceLastChat >= 3) {
        // 确保不是今天已经问候过
        const today = new Date().toDateString();
        if (lastGreetingCheck !== today) {
            showActiveGreeting();
            localStorage.setItem(ACTIVE_GREETING_KEY, today);
        }
    }

    localStorage.setItem(ACTIVE_GREETING_KEY, now.toString());
}

// 显示主动问候
function showActiveGreeting() {
    const hour = new Date().getHours();
    let greeting = '';
    let questions = [];

    if (hour >= 5 && hour < 12) {
        // 早上
        greeting = '早上好！';
        questions = [
            '昨晚睡得好吗？',
            '今天有什么计划吗？',
            '最近心情怎么样？'
        ];
    } else if (hour >= 12 && hour < 18) {
        // 下午
        greeting = '下午好！';
        questions = [
            '今天过得怎么样？',
            '有什么想分享的吗？',
            '工作/学习还顺利吗？'
        ];
    } else if (hour >= 18 && hour < 22) {
        // 晚上
        greeting = '晚上好！';
        questions = [
            '今天累不累？',
            '有什么开心的事吗？',
            '准备怎么放松一下？'
        ];
    } else {
        // 深夜
        greeting = '这么晚还没睡？';
        questions = [
            '睡不着吗？',
            '有什么心事吗？',
            '想聊聊吗？'
        ];
    }

    const daysSinceLastChat = Math.floor((Date.now() - parseInt(localStorage.getItem(LAST_CHAT_KEY))) / (1000 * 60 * 60 * 24));

    // 显示主动问候卡片
    const greetingCard = document.createElement('div');
    greetingCard.className = 'active-greeting-card';
    greetingCard.innerHTML = `
        <div class="greeting-header">
            <span class="greeting-emoji">👋</span>
            <span class="greeting-text">${greeting} 好久不见了</span>
            <button class="greeting-close" onclick="this.closest('.active-greeting-card').remove()">×</button>
        </div>
        <div class="greeting-content">
            <p>我们已经 ${daysSinceLastChat} 天没有聊天了，最近怎么样？</p>
            <p style="margin-top: 10px; color: #667eea;">有什么想和我分享的吗？</p>
        </div>
        <div class="greeting-actions">
            ${questions.map(q => `
                <button class="greeting-action-btn" onclick="answerGreeting('${q.replace(/'/g, "\\'")}')">
                    ${q}
                </button>
            `).join('')}
        </div>
    `;

    // 插入到聊天消息区域的顶部
    chatMessages.insertBefore(greetingCard, chatMessages.firstChild);
}

// 回应主动问候
window.answerGreeting = function(question) {
    messageInput.value = question;
    messageInput.focus();
    sendMessage();

    // 移除问候卡片
    const card = document.querySelector('.active-greeting-card');
    if (card) {
        card.remove();
    }
};

// 更新最后聊天时间
function updateLastChatTime() {
    localStorage.setItem(LAST_CHAT_KEY, Date.now().toString());
}

// ==================== 历史记录功能 ====================

const HISTORY_STORAGE_KEY = 'chat_history';
let conversationHistory = [];

// 加载历史记录
function loadHistory() {
    try {
        const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
        if (stored) {
            conversationHistory = JSON.parse(stored);
        }
    } catch (e) {
        console.error('加载历史记录失败:', e);
        conversationHistory = [];
    }
}

// 保存历史记录
function saveHistory() {
    try {
        localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(conversationHistory));
    } catch (e) {
        console.error('保存历史记录失败:', e);
    }
}

// 添加对话到历史记录
function addConversationToHistory(userMessage, botResponse, emotion, confidence) {
    const conversation = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        userMessage: userMessage,
        botResponse: botResponse,
        emotion: emotion,
        confidence: confidence
    };

    conversationHistory.unshift(conversation);

    // 只保留最近100条记录
    if (conversationHistory.length > 100) {
        conversationHistory = conversationHistory.slice(0, 100);
    }

    saveHistory();
}

// 格式化时间
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
        return '刚刚';
    } else if (diffMins < 60) {
        return `${diffMins}分钟前`;
    } else if (diffHours < 24) {
        return `${diffHours}小时前`;
    } else if (diffDays === 1) {
        return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays < 7) {
        const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        return weekdays[date.getDay()] + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else {
        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }) + ' ' +
               date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
}

// 格式化日期分组
function formatDateGroup(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today - 86400000);
    const itemDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    if (itemDate.getTime() === today.getTime()) {
        return '今天';
    } else if (itemDate.getTime() === yesterday.getTime()) {
        return '昨天';
    } else if (diffDays(date, now) < 7) {
        const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
        return weekdays[date.getDay()];
    } else {
        return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
    }
}

function diffDays(date1, date2) {
    const oneDay = 24 * 60 * 60 * 1000;
    const firstDate = new Date(date1.getFullYear(), date1.getMonth(), date1.getDate());
    const secondDate = new Date(date2.getFullYear(), date2.getMonth(), date2.getDate());
    return Math.round((firstDate - secondDate) / oneDay);
}

// 显示历史记录
async function displayHistory() {
    const historyList = document.getElementById('historyList');

    // 显示加载中
    historyList.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">加载中...</div>';

    try {
        // 从服务器加载历史记录
        const response = await fetch('/api/user/chat-messages?limit=50');
        const result = await response.json();

        if (!result.success || result.messages.length === 0) {
            historyList.innerHTML = `
                <div class="history-empty">
                    <div class="history-empty-icon">📭</div>
                    <div class="history-empty-text">暂无历史对话记录</div>
                    <div style="font-size: 0.85rem; color: #999; margin-top: 8px;">发送消息后将自动保存</div>
                </div>
            `;
            return;
        }

        // 按日期分组
        const groups = {};
        result.messages.forEach(msg => {
            const date = new Date(msg.created_at);
            const groupKey = formatDateGroup(date.toISOString());

            if (!groups[groupKey]) {
                groups[groupKey] = [];
            }

            groups[groupKey].push({
                id: msg.id,
                timestamp: msg.created_at,
                userMessage: msg.user_message,
                botResponse: msg.bot_response,
                emotion: msg.emotion,
                confidence: msg.confidence,
                strategyName: msg.strategy_name || null
            });
        });

        // 构建HTML
        let html = '';
        for (const [groupName, conversations] of Object.entries(groups)) {
            html += `
                <div class="history-date-group">
                    <div class="history-date-title">${groupName}</div>
            `;

            conversations.forEach(conv => {
                const emotionMap = {
                    'positive': { text: '积极', class: 'positive' },
                    'negative': { text: '消极', class: 'negative' },
                    'neutral': { text: '平静', class: 'neutral' }
                };
                const emotionData = emotionMap[conv.emotion] || emotionMap['neutral'];

                // 格式化时间
                const time = new Date(conv.timestamp);
                const timeStr = `${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}`;

                html += `
                    <div class="history-item" data-id="${conv.id}">
                        <div class="history-item-time">${timeStr}</div>
                        <div class="history-item-preview">
                            <div class="history-item-user">${conv.userMessage}</div>
                            <div class="history-item-emotion ${emotionData.class}">${emotionData.text}</div>
                        </div>
                        <button class="history-item-delete" onclick="deleteHistoryItem(event, ${conv.id})" title="删除此记录">
                            ×
                        </button>
                    </div>
                `;
            });

            html += `</div>`;
        }

        historyList.innerHTML = html;

        // 添加点击事件
        document.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', function() {
                const id = parseInt(this.dataset.id);
                loadConversationFromServer(id);
            });
        });

    } catch (error) {
        console.error('加载历史记录失败:', error);
        historyList.innerHTML = `
            <div style="text-align: center; padding: 20px; color: #f56565;">
                加载失败，请刷新页面重试
            </div>
        `;
    }
}

// 清空历史记录
function clearHistory() {
    if (confirm('确定要清空所有历史对话记录吗？此操作不可恢复。')) {
        conversationHistory = [];
        saveHistory();
        displayHistory();
    }
}

// 删除单条历史记录
async function deleteHistoryItem(event, messageId) {
    // 阻止事件冒泡，避免触发加载对话
    event.stopPropagation();

    if (!confirm('确定要删除这条对话记录吗？此操作不可恢复。')) {
        return;
    }

    try {
        const response = await fetch(`/api/user/chat-messages/${messageId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            console.log('✓ 已删除消息 ID:', messageId);
            // 重新加载历史记录
            displayHistory();
        } else {
            alert('删除失败：' + (result.error || '未知错误'));
        }
    } catch (error) {
        console.error('删除消息失败:', error);
        alert('删除失败，请稍后重试');
    }
}

// 打开历史记录模态框
function openHistoryModal() {
    const modal = document.getElementById('historyModal');
    modal.classList.add('show');
    displayHistory();
}

// 关闭历史记录模态框
function closeHistoryModal() {
    const modal = document.getElementById('historyModal');
    modal.classList.remove('show');
}

// 从服务器加载特定对话及其上下文
async function loadConversationFromServer(id) {
    try {
        // 获取更多历史记录以便找到上下文
        const response = await fetch(`/api/user/chat-messages?limit=200`);
        const result = await response.json();

        if (result.success) {
            // 找到选中的消息在列表中的索引
            const selectedIndex = result.messages.findIndex(m => m.id === id);

            if (selectedIndex !== -1) {
                // 获取上下文：前后各3条消息，总共显示约7条
                const contextSize = 3;
                const startIndex = Math.max(0, selectedIndex - contextSize);
                const endIndex = Math.min(result.messages.length - 1, selectedIndex + contextSize);

                // 获取上下文范围内的消息（注意：messages是按时间倒序排列的）
                const contextMessages = result.messages.slice(startIndex, endIndex + 1);

                // 清空当前聊天记录
                chatMessages.innerHTML = '';

                // 按时间正序添加消息（因为messages是倒序的，所以需要反转）
                for (let i = contextMessages.length - 1; i >= 0; i--) {
                    const msg = contextMessages[i];

                    // 添加用户消息
                    addMessage(msg.user_message, 'user');

                    // 添加机器人回复
                    addMessage(msg.bot_response, 'bot', msg.id);
                }

                // 关闭模态框
                closeHistoryModal();

                // 滚动到底部
                scrollToBottom();

                console.log(`✓ 已加载 ${contextMessages.length} 轮对话（包含上下文）`);
            }
        }
    } catch (error) {
        console.error('加载对话失败:', error);
    }
}

// 加载特定对话（已弃用 - 使用 loadConversationFromServer）
function loadConversation(id) {
    // 这个函数已弃用，请使用 loadConversationFromServer
    console.warn('loadConversation 已弃用，使用 loadConversationFromServer 代替');
    loadConversationFromServer(id);
}

// 事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 加载历史记录
    loadHistory();

    // 检查是否需要主动问候
    checkActiveGreeting();

    // 历史记录按钮
    const historyBtn = document.getElementById('historyBtn');
    if (historyBtn) {
        historyBtn.addEventListener('click', openHistoryModal);
    }

    // 关闭按钮
    const closeHistoryBtn = document.getElementById('closeHistoryBtn');
    if (closeHistoryBtn) {
        closeHistoryBtn.addEventListener('click', closeHistoryModal);
    }

    // 清空历史按钮
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', clearHistory);
    }

    // 点击模态框背景关闭
    const historyModal = document.getElementById('historyModal');
    if (historyModal) {
        historyModal.addEventListener('click', function(e) {
            if (e.target === historyModal) {
                closeHistoryModal();
            }
        });
    }

    // ESC键关闭模态框
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeHistoryModal();
        }
    });
});

// 自动调整文本框高度
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// 发送消息
async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) return;

    // 禁用输入
    messageInput.disabled = true;
    sendBtn.disabled = true;

    // 添加用户消息
    addMessage(message, 'user');

    // 清空输入框
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // 显示输入指示器
    showTypingIndicator();

    // 机器人进入思考状态
    updateRobotState('thinking');

    // 滚动到底部
    scrollToBottom();

    try {
        // 发送到后端
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        // 移除输入指示器
        hideTypingIndicator();

        if (data.success) {
            // 根据情绪更新机器人状态
            if (data.emotion === 'positive') {
                updateRobotState('happy', data.emotion);
            } else if (data.emotion === 'negative') {
                updateRobotState('concerned', data.emotion);
            } else {
                updateRobotState('ready', data.emotion);
            }

            // 添加AI回复
            addMessage(data.response, 'bot', data.chat_message_id);

            // 提取并显示AI的主动询问
            extractAndShowAIQuestions(data.response);

            // 更新"猜你想问"
            updateSuggestedQuestions(data.follow_up_questions);

            // 更新最后聊天时间
            updateLastChatTime();

            // 保存对话到历史记录
            addConversationToHistory(message, data.response, data.emotion, data.confidence);

            // 播放TTS语音（同时触发说话动画）
            if (data.audio_path) {
                await playAudioWithAnimation(data.audio_path);
            }
        } else {
            addMessage('抱歉，我遇到了一些问题。', 'bot');
            updateRobotState('default');
        }

    } catch (error) {
        console.error('Error:', error);
        hideTypingIndicator();
        addMessage('抱歉，连接服务器失败。', 'bot');
        updateRobotState('default');
    }

    // 重新启用输入
    messageInput.disabled = false;
    sendBtn.disabled = false;
    messageInput.focus();

    // 滚动到底部
    scrollToBottom();
}

// 添加消息到聊天界面
function addMessage(content, type, chatMessageId = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    if (chatMessageId) {
        messageDiv.dataset.messageId = chatMessageId;
    }

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? '👤' : '🧠';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    // 为bot消息添加反馈按钮
    if (type === 'bot' && chatMessageId) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'message-feedback';

        const thumbsUpBtn = document.createElement('button');
        thumbsUpBtn.className = 'feedback-btn feedback-positive';
        thumbsUpBtn.innerHTML = '👍';
        thumbsUpBtn.title = '有帮助';
        thumbsUpBtn.onclick = () => submitFeedback(chatMessageId, 'positive', thumbsUpBtn);

        const thumbsDownBtn = document.createElement('button');
        thumbsDownBtn.className = 'feedback-btn feedback-negative';
        thumbsDownBtn.innerHTML = '👎';
        thumbsDownBtn.title = '有问题';
        thumbsDownBtn.onclick = () => showFeedbackReasons(chatMessageId, thumbsDownBtn);

        feedbackDiv.appendChild(thumbsUpBtn);
        feedbackDiv.appendChild(thumbsDownBtn);
        messageDiv.appendChild(feedbackDiv);
    }

    chatMessages.appendChild(messageDiv);
}

// 显示输入指示器
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing-message';
    typingDiv.innerHTML = `
        <div class="message-avatar">🧠</div>
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
}

// 隐藏输入指示器
function hideTypingIndicator() {
    const typingMessage = chatMessages.querySelector('.typing-message');
    if (typingMessage) {
        typingMessage.remove();
    }
}

// 滚动到底部
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 播放音频
function playAudio(audioPath) {
    audioPlayer.src = audioPath;
    audioPlayer.play().catch(e => console.log('音频播放失败:', e));
}

// 播放音频并触发说话动画
function playAudioWithAnimation(audioPath) {
    return new Promise((resolve) => {
        // 机器人进入说话状态
        updateRobotState('talking');

        audioPlayer.src = audioPath;

        // 音频播放结束后停止动画
        audioPlayer.onended = () => {
            stopTalking();
            resolve();
        };

        // 如果播放失败，也要停止动画
        audioPlayer.onerror = () => {
            console.log('音频播放失败');
            stopTalking();
            resolve();
        };

        audioPlayer.play().catch(e => {
            console.log('音频播放失败:', e);
            stopTalking();
            resolve();
        });
    });
}

// 停止说话动画
function stopTalking() {
    robotMouth.classList.remove('talking');
    // 恢复默认状态
    updateRobotState('default', 'neutral');
}

// ========== 录音功能 ==========

// 录音开始时间
let recordingStartTime = null;
// 最短录音时长（毫秒）
const MIN_RECORDING_DURATION = 800; // 至少0.8秒

// 开始录音
async function startRecording() {
    try {
        // 清理之前的录音状态
        if (mediaRecorder) {
            mediaRecorder.ondataavailable = null;
            mediaRecorder.onstop = null;
            mediaRecorder = null;
        }
        audioChunks = [];

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // 检测浏览器支持的音频格式
        let options = {};
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4',
            'audio/mpeg'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                options = { mimeType: type };
                console.log('使用音频格式:', type);
                break;
            }
        }

        mediaRecorder = new MediaRecorder(stream, options);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                audioChunks.push(event.data);
                console.log(`收到音频数据块: ${event.data.size} bytes, 累计 ${audioChunks.length} 个块`);
            }
        };

        mediaRecorder.onstop = async () => {
            // 计算录音时长
            const recordingDuration = Date.now() - recordingStartTime;
            console.log(`录音停止，时长: ${recordingDuration}ms，数据块: ${audioChunks.length} 个`);

            // 检查录音时长是否太短
            if (recordingDuration < MIN_RECORDING_DURATION) {
                console.warn(`录音时长太短 (${recordingDuration}ms < ${MIN_RECORDING_DURATION}ms)`);
                alert(`录音时间太短（${recordingDuration/1000}秒），请至少说话 ${MIN_RECORDING_DURATION/1000} 秒`);
                return;
            }

            if (audioChunks.length === 0) {
                console.error('没有收到任何音频数据！');
                alert('未收到音频数据，请重新录音');
                return;
            }

            // 使用第一个数据块的类型，或者使用浏览器默认类型
            const mimeType = audioChunks[0]?.type || 'audio/webm';
            const audioBlob = new Blob(audioChunks, { type: mimeType });
            console.log(`音频Blob: ${audioBlob.size} bytes, type: ${mimeType}`);
            await sendAudio(audioBlob);
        };

        // 记录开始时间
        recordingStartTime = Date.now();
        console.log('开始录音...');

        // 每250ms触发一次ondataavailable，确保持续收集数据
        mediaRecorder.start(250);
        isRecording = true;
        recordBtn.classList.add('recording');
        statusDiv.textContent = '🔴 正在录音...';

    } catch (error) {
        console.error('录音错误:', error);
        alert('无法访问麦克风，请检查权限设置。');
    }
}

// 停止录音
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        recordBtn.classList.remove('recording');
        statusDiv.textContent = '系统就绪';
    }
}

// 发送音频到后端
async function sendAudio(audioBlob) {
    showTypingIndicator();
    scrollToBottom();

    // 根据MIME类型确定文件扩展名
    const mimeType = audioBlob.type || 'audio/webm';
    let extension = 'webm';
    if (mimeType.includes('ogg')) extension = 'ogg';
    else if (mimeType.includes('mp4') || mimeType.includes('mpeg')) extension = 'mp4';
    else if (mimeType.includes('wav')) extension = 'wav';

    const formData = new FormData();
    formData.append('audio', audioBlob, `recording.${extension}`);

    try {
        const response = await fetch('/api/audio', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        hideTypingIndicator();

        if (data.success && data.text) {
            // 检查文本长度，避免处理极短文本
            if (data.text.trim().length < 2) {
                console.warn('识别文本太短，忽略:', data.text);
                alert('未识别到有效语音，请重新说话');
                return;
            }

            // 准备聊天请求数据
            const chatRequestData = {
                message: data.text
            };

            // 如果有语音情绪数据，传递给聊天API
            if (data.voice_emotion) {
                chatRequestData.voice_emotion = data.voice_emotion;
                console.log('语音情绪分析:', data.voice_emotion);
            }

            // 直接调用聊天API（而不是通过sendMessage，避免重复添加消息）
            try {
                const chatResponse = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(chatRequestData)
                });

                const chatData = await chatResponse.json();

                if (chatData.success) {
                    // 成功后才添加用户消息和AI回复
                    addMessage(data.text, 'user');
                    addMessage(chatData.response, 'bot', chatData.chat_message_id);

                    // 显示情绪分析结果
                    if (chatData.emotion_method) {
                        console.log(`情绪分析方式: ${chatData.emotion_method}`);
                        if (chatData.emotion_method === 'multimodal_fusion' && chatData.emotion_details) {
                            console.log(`文字情绪: ${chatData.emotion_details.text_emotion}, 语音情绪: ${chatData.emotion_details.voice_emotion}`);
                            console.log(`融合权重 - 文字: ${chatData.emotion_details.text_weight}, 语音: ${chatData.emotion_details.voice_weight}`);
                        }
                    }

                    // 根据情绪更新机器人状态
                    if (chatData.emotion === 'positive') {
                        updateRobotState('happy', chatData.emotion);
                    } else if (chatData.emotion === 'negative') {
                        updateRobotState('concerned', chatData.emotion);
                    } else {
                        updateRobotState('ready', chatData.emotion);
                    }

                    // 保存对话到历史记录
                    addConversationToHistory(data.text, chatData.response, chatData.emotion, chatData.confidence);

                    // 播放TTS语音
                    if (chatData.audio_path) {
                        await playAudioWithAnimation(chatData.audio_path);
                    }
                } else {
                    // 聊天API失败
                    console.error('聊天API失败:', chatData.error);
                    alert('对话生成失败: ' + (chatData.error || '未知错误'));
                }
            } catch (chatError) {
                console.error('聊天API调用错误:', chatError);
                alert('对话生成出错: ' + chatError.message);
            }
        } else if (data.success && !data.text) {
            // 成功但没有识别到文本
            alert('未识别到语音，请说话清晰一些并确保至少说话1秒');
        } else {
            // 显示错误信息
            const errorMsg = data.error || '未知错误';
            console.error('语音识别失败:', errorMsg);
            alert('语音识别失败: ' + errorMsg);
        }

    } catch (error) {
        console.error('Error:', error);
        hideTypingIndicator();
        alert('语音识别出错: ' + error.message);
    }
}

// ==================== 反馈功能 ====================

// 提交正面反馈
async function submitFeedback(chatMessageId, feedbackType, buttonElement) {
    try {
        const response = await fetch('/api/chat/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_message_id: chatMessageId,
                feedback_type: feedbackType,
                feedback_reason: 'helpful'
            })
        });

        const data = await response.json();

        if (data.success) {
            // 禁用反馈按钮
            const feedbackDiv = buttonElement.parentElement;
            const buttons = feedbackDiv.querySelectorAll('.feedback-btn');
            buttons.forEach(btn => btn.disabled = true);

            // 显示成功提示
            buttonElement.textContent = '✓';
            buttonElement.classList.add('feedback-submitted');

            console.log('反馈提交成功:', data.feedback_id);
        } else {
            alert('反馈提交失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('提交反馈错误:', error);
        alert('提交反馈时出错: ' + error.message);
    }
}

// 显示负面反馈原因选择
function showFeedbackReasons(chatMessageId, buttonElement) {
    const reasons = [
        { value: 'inappropriate', label: '内容不当' },
        { value: 'inaccurate', label: '理解错误' },
        { value: 'unclear', label: '不够清晰' },
        { value: 'other', label: '其他问题' }
    ];

    // 创建选择对话框
    const modal = document.createElement('div');
    modal.className = 'feedback-modal';
    modal.innerHTML = `
        <div class="feedback-modal-content">
            <h3>请选择问题原因</h3>
            <div class="feedback-reasons">
                ${reasons.map(r => `
                    <button class="feedback-reason-btn" data-reason="${r.value}">
                        ${r.label}
                    </button>
                `).join('')}
            </div>
            <div class="feedback-modal-actions">
                <button class="feedback-cancel-btn">取消</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // 添加事件监听
    modal.querySelectorAll('.feedback-reason-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const reason = btn.dataset.reason;
            await submitNegativeFeedback(chatMessageId, reason, buttonElement);
            document.body.removeChild(modal);
        });
    });

    modal.querySelector('.feedback-cancel-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
    });

    // 点击背景关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

// 提交负面反馈
async function submitNegativeFeedback(chatMessageId, feedbackReason, buttonElement) {
    try {
        const response = await fetch('/api/chat/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_message_id: chatMessageId,
                feedback_type: 'negative',
                feedback_reason: feedbackReason
            })
        });

        const data = await response.json();

        if (data.success) {
            // 禁用反馈按钮
            const feedbackDiv = buttonElement.parentElement;
            const buttons = feedbackDiv.querySelectorAll('.feedback-btn');
            buttons.forEach(btn => btn.disabled = true);

            // 显示已提交标记
            buttonElement.textContent = '✓';
            buttonElement.classList.add('feedback-submitted');

            console.log('负面反馈提交成功:', data.feedback_id);
        } else {
            alert('反馈提交失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('提交反馈错误:', error);
        alert('提交反馈时出错: ' + error.message);
    }
}

// 录音按钮事件
recordBtn.addEventListener('mousedown', (e) => {
    e.preventDefault();
    startRecording();
});

recordBtn.addEventListener('mouseup', () => {
    stopRecording();
});

recordBtn.addEventListener('mouseleave', () => {
    if (isRecording) {
        stopRecording();
    }
});

// 触摸设备支持
recordBtn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    startRecording();
});

recordBtn.addEventListener('touchend', (e) => {
    e.preventDefault();
    stopRecording();
});

// ========== 事件监听 ==========

sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', function(e) {
    // Ctrl+Enter 发送
    if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ==================== 机器人控制 ====================

const robot = document.getElementById('robot');
const robotHead = robot.querySelector('.robot-head');
const robotBody = robot.querySelector('.robot-body');
const robotMouth = document.getElementById('robotMouth');
const avatarStatus = document.getElementById('avatarStatus');
const eyes = document.querySelectorAll('.eye');

// 眨眼动画（随机间隔）
function blink() {
    eyes.forEach(eye => {
        eye.classList.add('blink');
        setTimeout(() => eye.classList.remove('blink'), 200);
    });
    // 随机2-6秒后再次眨眼
    setTimeout(blink, Math.random() * 4000 + 2000);
}

// 更新机器人状态
function updateRobotState(state, emotion = 'neutral') {
    // 移除所有状态类
    robotHead.classList.remove('positive', 'negative', 'thinking');
    robotBody.classList.remove('positive', 'negative', 'thinking');
    robotMouth.classList.remove('talking', 'happy', 'surprised');

    // 先根据情绪设置颜色
    if (emotion === 'positive') {
        robotHead.classList.add('positive');
        robotBody.classList.add('positive');
    } else if (emotion === 'negative') {
        robotHead.classList.add('negative');
        robotBody.classList.add('negative');
    }

    // 然后根据状态设置动作和表情
    switch(state) {
        case 'listening':
            avatarStatus.textContent = '👂 我在听...';
            robotMouth.classList.add('happy');
            break;
        case 'thinking':
            avatarStatus.textContent = '🤔 思考中...';
            robotHead.classList.add('thinking');
            robotBody.classList.add('thinking');
            break;
        case 'ready':
            avatarStatus.textContent = '✨ 准备回答';
            break;
        case 'talking':
            avatarStatus.textContent = '💬 正在说话...';
            robotMouth.classList.add('talking');
            break;
        case 'happy':
            avatarStatus.textContent = '😊 很高兴能帮到你！';
            robotMouth.classList.add('happy');
            break;
        case 'concerned':
            avatarStatus.textContent = '💙 我理解你的感受...';
            robotMouth.classList.add('happy');
            break;
        default:
            avatarStatus.textContent = '👋 你好呀~';
    }
}

// 页面加载时启动眨眼动画
window.addEventListener('load', function() {
    messageInput.focus();
    statusDiv.textContent = '✅ 系统就绪 | MindChat 对话系统已加载 | 按住🎤说话';

    // 启动眨眼动画
    setTimeout(blink, 2000);
});



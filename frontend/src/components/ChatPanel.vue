<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import type { ChatMessage } from '@/stores/analysis'

interface Props {
  messages: ChatMessage[]
  loading: boolean
  placeholder?: string
  examples?: string[]
}

interface Emits {
  (e: 'send', message: string): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '输入分析指令，例如：\'计算各组的均值和标准差\'...',
  examples: () => [
    '查看数据的基本统计信息',
    '绘制各列的相关性热力图',
    '对数值列进行描述性统计',
  ],
})

const emit = defineEmits<Emits>()

const inputValue = ref('')
const chatContainer = ref<HTMLElement | null>(null)

async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

watch(() => props.messages.length, () => scrollToBottom())

onMounted(() => scrollToBottom())

function handleSend() {
  const msg = inputValue.value.trim()
  if (!msg || props.loading) return
  emit('send', msg)
  inputValue.value = ''
}
</script>

<template>
  <div class="chat-panel">
    <div class="chat-header">
      <h3>对话</h3>
    </div>
    <div ref="chatContainer" class="chat-messages">
      <div v-if="messages.length === 0" class="chat-empty">
        <n-icon size="48" color="#63e2b7">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </n-icon>
        <p>发送自然语言指令开始分析数据</p>
        <div class="example-prompts">
          <n-tag
            v-for="p in examples"
            :key="p"
            class="example-tag"
            @click="emit('send', p)"
          >
            {{ p }}
          </n-tag>
        </div>
      </div>
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        class="chat-message"
        :class="msg.role"
      >
        <div class="message-avatar">
          <n-icon v-if="msg.role === 'user'" size="20">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </n-icon>
          <n-icon v-else size="20">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z" />
              <path d="M12 6v6l4 2" />
            </svg>
          </n-icon>
        </div>
        <div class="message-content">
          <div class="message-text">{{ msg.content }}</div>
          <div v-if="msg.status" class="message-status">
            <n-tag
              size="tiny"
              :type="msg.status === 'thinking' ? 'info' : msg.status === 'coding' ? 'warning' : msg.status === 'executing' ? 'default' : 'success'"
            >
              {{ msg.statusLabel }}
            </n-tag>
          </div>
        </div>
      </div>
      <div v-if="loading" class="chat-message assistant">
        <div class="message-avatar">
          <n-icon size="20">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
            </svg>
          </n-icon>
        </div>
        <div class="message-content">
          <div class="typing-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>
    </div>
    <div class="chat-input-area">
      <n-input
        v-model:value="inputValue"
        type="textarea"
        :placeholder="placeholder"
        :autosize="{ minRows: 1, maxRows: 4 }"
        :disabled="loading"
        @keydown.enter.exact.prevent="handleSend"
        round
        clearable
      />
      <n-button
        type="primary"
        :loading="loading"
        :disabled="!inputValue.trim()"
        @click="handleSend"
        round
        class="send-btn"
      >
        发送
      </n-button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #181d23;
}

.chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.chat-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e8edf2;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666d78;
  gap: 12px;
}

.chat-empty p {
  font-size: 14px;
}

.example-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}

.example-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.example-tag:hover {
  opacity: 0.8;
  transform: translateY(-1px);
}

.chat-message {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.chat-message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.chat-message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(99, 226, 183, 0.12);
  color: #63e2b7;
}

.chat-message.user .message-avatar {
  background: rgba(99, 160, 226, 0.12);
  color: #63a0e2;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message-text {
  padding: 10px 16px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-message.user .message-text {
  background: linear-gradient(135deg, #63a0e2, #4d8bd4);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-message.assistant .message-text {
  background: rgba(255, 255, 255, 0.1);
  color: #e0e4e9;
  border-bottom-left-radius: 4px;
}

.message-status {
  padding-left: 4px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 10px 16px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #63e2b7;
  animation: typing 1.4s infinite ease-in-out;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}

.chat-input-area {
  padding: 12px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.send-btn {
  flex-shrink: 0;
}
</style>

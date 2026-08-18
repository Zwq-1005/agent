<script setup lang="ts">
import { ref, onUnmounted, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { useRouter } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysis'
import { streamAnalysis, downloadReport } from '@/api/analysis'
import ChatPanel from '@/components/ChatPanel.vue'
import ResultPanel from '@/components/ResultPanel.vue'

const store = useAnalysisStore()
const message = useMessage()
const router = useRouter()
const exporting = ref(false)
const exportFormat = ref<'word' | 'pdf'>('word')
let abortController: AbortController | null = null

// Redirect to import if no session
if (!store.sessionId) {
  router.replace('/import')
}

const hasFieldDefinitions = computed(() => store.fieldDefinitions.length > 0)

function handleSend(msg: string) {
  if (!store.sessionId) {
    message.warning('请先上传数据文件')
    router.push('/import')
    return
  }

  if (!hasFieldDefinitions.value) {
    message.warning('请先在"数据导入"中定义字段并应用更改')
    return
  }

  store.addMessage({ role: 'user', content: msg })
  store.setLoading(true)
  store.clearResults()

  abortController = streamAnalysis(
    store.sessionId,
    msg,
    store.fieldDefinitions,
    store.activeFileId,
    (event, data) => {
      switch (event) {
        case 'thinking':
          store.addMessage({
            role: 'assistant',
            content: data,
            status: 'thinking',
            statusLabel: 'AI 正在思考...',
          })
          break
        case 'coding':
          try {
            const parsed = JSON.parse(data)
            store.addResult({ type: 'code', content: parsed.code, title: '📝 生成的分析代码' })
          } catch {
            store.addResult({ type: 'code', content: data, title: '📝 生成的代码' })
          }
          break
        case 'executing':
          store.addMessage({
            role: 'assistant',
            content: data,
            status: 'executing',
            statusLabel: '正在执行...',
          })
          break
        case 'result':
          try {
            const result = JSON.parse(data)
            store.addResult({
              type: result.type || 'text',
              content: result.content,
              title: result.title,
              columns: result.columns,
              rows: result.rows,
            })
          } catch {
            store.addResult({ type: 'text', content: data, title: '📋 分析结果' })
          }
          break
        case 'paper_text':
          store.addResult({ type: 'text', content: data, title: '📄 论文描述文本' })
          break
        case 'done':
          store.addMessage({
            role: 'assistant',
            content: data || '✅ 分析完成',
            status: 'done',
            statusLabel: '完成',
          })
          break
        case 'error':
          try {
            const errData = JSON.parse(data)
            store.addResult({ type: 'error', content: errData.content, title: errData.title || '⚠️ 错误' })
          } catch {
            store.addResult({ type: 'error', content: data, title: '⚠️ 错误' })
          }
          break
      }
    },
    (err) => {
      message.error('连接分析服务失败，请检查后端是否运行')
      store.setLoading(false)
    },
    () => {
      store.setLoading(false)
    }
  )
}

async function handleExport(format: 'word' | 'pdf') {
  if (!store.sessionId) {
    message.warning('没有可导出的会话')
    return
  }
  exporting.value = true
  try {
    await downloadReport(store.sessionId, format, store.activeFileId || undefined)
    message.success(`${format === 'word' ? 'Word' : 'PDF'} 报告下载成功！`)
  } catch (err: any) {
    message.error('导出失败：' + (err.message || '请检查后端服务'))
  } finally {
    exporting.value = false
  }
}

function goToPrompts() { router.push('/prompts') }
function goToImport() { router.push('/import') }

onUnmounted(() => {
  abortController?.abort()
})
</script>

<template>
  <div class="worksbench-page">
    <!-- No session state -->
    <div v-if="!store.sessionId" class="no-session">
      <n-icon size="48" color="#63e2b7">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </n-icon>
      <p>请先完成以下步骤：</p>
      <div class="steps-hint">
        <div class="step-hint done"><span class="step-num">1</span> 数据导入和字段定义</div>
        <div class="step-hint done"><span class="step-num">2</span> 数据清洗</div>
        <div class="step-hint active"><span class="step-num">3</span> 选择 Prompt 模板</div>
        <div class="step-hint"><span class="step-num">4</span> AI 自动分析</div>
      </div>
      <n-button type="primary" @click="goToImport">去导入数据</n-button>
    </div>

    <!-- No field definitions state -->
    <div v-else-if="!hasFieldDefinitions" class="no-session">
      <n-icon size="48" color="#f0a04b">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      </n-icon>
      <p>请先在"数据导入"中定义字段并点击"应用更改"</p>
      <n-button type="warning" @click="goToImport">去定义字段</n-button>
    </div>

    <!-- Main workspace -->
    <div v-else class="worksbench-layout">
      <div class="panel-left">
        <ChatPanel
          :messages="store.messages"
          :loading="store.loading"
          @send="handleSend"
        />
      </div>
      <div class="panel-right">
        <!-- Export toolbar -->
        <div class="result-toolbar">
          <span class="toolbar-title">分析结果</span>
          <n-space>
            <n-button-group size="small">
              <n-button :type="exportFormat === 'word' ? 'primary' : 'default'" @click="exportFormat = 'word'">
                Word
              </n-button>
              <n-button :type="exportFormat === 'pdf' ? 'primary' : 'default'" @click="exportFormat = 'pdf'">
                PDF
              </n-button>
            </n-button-group>
            <n-button
              type="primary"
              size="small"
              :loading="exporting"
              @click="handleExport(exportFormat)"
            >
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                </n-icon>
              </template>
              下载{{ exportFormat === 'word' ? 'Word' : 'PDF' }}报告
            </n-button>
          </n-space>
        </div>
        <ResultPanel :results="store.results" />

        <!-- Prompt quick-access -->
        <div v-if="store.results.length === 0 && !store.loading" class="prompt-hint">
          <p class="hint-text">💡 需要分析灵感？</p>
          <n-button text type="primary" @click="goToPrompts">查看 Prompt 模板 →</n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.worksbench-page { height: calc(100vh - 90px); overflow: hidden; }

.worksbench-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  height: 100%;
  gap: 1px;
  background: #1a1f26;
}

.panel-left, .panel-right { height: 100%; overflow: hidden; }

.result-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #12161c;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.toolbar-title { font-size: 14px; font-weight: 600; color: #c0c7d0; }

.no-session {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; gap: 16px; color: #7d8692;
}

.steps-hint { display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }

.step-hint {
  display: flex; align-items: center; gap: 8px; font-size: 14px; color: #5c6672;
}

.step-hint .step-num {
  width: 24px; height: 24px; border-radius: 50%;
  background: rgba(255,255,255,0.1);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600;
  color: #a0aab4;
}

.step-hint.done .step-num { background: rgba(99,226,183,0.2); color: #63e2b7; }
.step-hint.active { color: #63e2b7; }
.step-hint.done { color: #7d8692; text-decoration: line-through; text-decoration-color: rgba(99,226,183,0.3); }

.prompt-hint {
  padding: 16px; text-align: center;
  border-top: 1px solid rgba(255,255,255,0.04);
}

.hint-text { color: #7d8692; font-size: 13px; margin-bottom: 4px; }

@media (max-width: 768px) {
  .worksbench-layout { grid-template-columns: 1fr; grid-template-rows: 1fr 1fr; }
}
</style>

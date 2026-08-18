import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { FieldDefinition } from '@/api/analysis'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  status?: 'thinking' | 'coding' | 'executing' | 'done'
  statusLabel?: string
}

export interface ResultItem {
  type: 'text' | 'table' | 'chart' | 'error' | 'code'
  content: string
  title?: string
  columns?: { title: string; key: string }[]
  rows?: Record<string, unknown>[]
}

export const useAnalysisStore = defineStore('analysis', () => {
  const sessionId = ref<number | null>(null)
  const fileId = ref<number | null>(null)
  const cleanedFileId = ref<number | null>(null)
  const messages = ref<ChatMessage[]>([])
  const results = ref<ResultItem[]>([])
  const loading = ref(false)
  const fieldDefinitions = ref<FieldDefinition[]>([])
  const vipTier = ref<'basic' | 'vip'>('basic')
  const currentStep = ref<number>(1)  // 1=import, 2=clean, 3=prompts, 4=analyze

  const hasSession = computed(() => sessionId.value !== null)
  const hasFile = computed(() => fileId.value !== null)
  const hasFieldDefinitions = computed(() => fieldDefinitions.value.length > 0)
  const activeFileId = computed(() => cleanedFileId.value || fileId.value)

  function setSessionId(id: number) {
    sessionId.value = id
  }

  function setFileId(id: number) {
    fileId.value = id
    cleanedFileId.value = null
  }

  function setCleanedFileId(id: number) {
    cleanedFileId.value = id
  }

  function setFieldDefinitions(fields: FieldDefinition[]) {
    fieldDefinitions.value = fields
  }

  function addMessage(msg: ChatMessage) {
    messages.value.push(msg)
  }

  function addResult(result: ResultItem) {
    results.value.push(result)
  }

  function clearResults() {
    results.value = []
  }

  function clearMessages() {
    messages.value = []
  }

  function setLoading(val: boolean) {
    loading.value = val
  }

  function setVipTier(tier: 'basic' | 'vip') {
    vipTier.value = tier
  }

  function setCurrentStep(step: number) {
    currentStep.value = step
  }

  function getFileSizeLimit(): number {
    return vipTier.value === 'vip' ? 20 * 1024 * 1024 : 1 * 1024 * 1024
  }

  function reset() {
    sessionId.value = null
    fileId.value = null
    cleanedFileId.value = null
    messages.value = []
    results.value = []
    loading.value = false
    fieldDefinitions.value = []
    currentStep.value = 1
  }

  return {
    sessionId,
    fileId,
    cleanedFileId,
    messages,
    results,
    loading,
    fieldDefinitions,
    vipTier,
    currentStep,
    hasSession,
    hasFile,
    hasFieldDefinitions,
    activeFileId,
    setSessionId,
    setFileId,
    setCleanedFileId,
    setFieldDefinitions,
    addMessage,
    addResult,
    clearResults,
    clearMessages,
    setLoading,
    setVipTier,
    setCurrentStep,
    getFileSizeLimit,
    reset,
  }
})

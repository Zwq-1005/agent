import apiClient from './client'

// ─── Types ────────────────────────────────────────────────────────────────────────

export interface FieldDefinition {
  original_name: string
  display_name: string
  field_type: 'numeric' | 'categorical' | 'ordinal' | 'datetime' | 'text' | 'id'
  unit?: string
  description?: string
  levels?: string  // comma-separated levels for categorical
}

export interface UploadedFileInfo {
  id: number
  filename: string
  file_type: string
  columns: string[]
  row_count: number
}

export interface PreviewData {
  file_id: number
  session_id: number
  filename: string
  columns: string[]
  preview_rows: Record<string, unknown>[]
  total_rows: number
  fields?: FieldDefinition[]
}

export interface QualityReport {
  total_rows: number
  total_columns: number
  duplicate_rows: number
  duplicate_pct: number
  total_missing: number
  missing_pct: number
  columns: QualityColumnInfo[]
}

export interface QualityColumnInfo {
  column: string
  dtype: string
  missing_count: number
  missing_pct: number
  unique_count: number
  duplicate_pct: number
  min?: number
  max?: number
  mean?: number
  std?: number
  outlier_count?: number
  outlier_pct?: number
  top_values?: Record<string, number>
}

export interface CleaningRequest {
  file_id: number
  drop_duplicates: boolean
  fill_numeric: string | null
  fill_categorical: string | null
  remove_outliers: boolean
  outlier_columns: string[] | null
}

export interface CleaningResult extends PreviewData {
  cleaning_summary: {
    rows_before: number
    rows_after: number
    total_removed: number
    actions: Array<{
      action: string
      message: string
      [key: string]: unknown
    }>
  }
}

export interface AutoStats {
  [column: string]: {
    type: 'numeric' | 'categorical'
    count: number
    [key: string]: unknown
  }
}

export interface AnalysisSession {
  id: number
  title: string
  status: string
  created_at: string
  updated_at: string
  files?: UploadedFileInfo[]
  messages?: ChatMessage[]
}

export interface ChatMessage {
  id: number
  session_id: number
  role: string
  content: string
  status?: string
  status_label?: string
  created_at: string
}

export interface PromptTemplate {
  id: number
  name: string
  category: string
  content: string
  description: string
  is_default: boolean
  created_at: string
}

// ─── Upload ───────────────────────────────────────────────────────────────────────

export async function uploadFile(
  file: File,
  sessionId?: number,
  fileSizeLimit: number = 1 * 1024 * 1024
): Promise<PreviewData> {
  if (file.size > fileSizeLimit) {
    const limitMB = fileSizeLimit / (1024 * 1024)
    throw new Error(`文件大小超过 ${limitMB}MB 限制。基础版限制 1MB，VIP 限制 20MB。`)
  }

  const formData = new FormData()
  formData.append('file', file)
  if (sessionId) {
    formData.append('session_id', String(sessionId))
  }
  const { data } = await apiClient.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getFilePreview(fileId: number): Promise<PreviewData> {
  const { data } = await apiClient.get(`/upload/preview/${fileId}`)
  return data
}

// ─── Field Definitions ────────────────────────────────────────────────────────────

export async function saveFieldDefinitions(
  fileId: number,
  fields: FieldDefinition[]
): Promise<{ success: boolean }> {
  const { data } = await apiClient.put(`/upload/${fileId}/fields`, { fields })
  return data
}

export async function getFieldDefinitions(fileId: number): Promise<FieldDefinition[]> {
  const { data } = await apiClient.get(`/upload/${fileId}/fields`)
  return data
}

// ─── Data Quality & Cleaning ──────────────────────────────────────────────────────

export async function getQualityReport(fileId: number): Promise<QualityReport> {
  const { data } = await apiClient.get(`/upload/${fileId}/quality`)
  return data
}

export async function cleanData(req: CleaningRequest): Promise<CleaningResult> {
  const { data } = await apiClient.post('/upload/clean', req)
  return data
}

// ─── Auto Statistics ──────────────────────────────────────────────────────────────

export async function getAutoStats(fileId: number): Promise<AutoStats> {
  const { data } = await apiClient.get(`/upload/${fileId}/auto-stats`)
  return data
}

// ─── Sessions ─────────────────────────────────────────────────────────────────────

export async function createSession(title: string): Promise<AnalysisSession> {
  const { data } = await apiClient.post('/sessions', { title })
  return data
}

export async function listSessions(): Promise<AnalysisSession[]> {
  const { data } = await apiClient.get('/sessions')
  return data
}

export async function getSession(sessionId: number): Promise<AnalysisSession> {
  const { data } = await apiClient.get(`/sessions/${sessionId}`)
  return data
}

export async function updateSession(
  sessionId: number,
  updates: Partial<Pick<AnalysisSession, 'title' | 'status'>>
): Promise<AnalysisSession> {
  const { data } = await apiClient.put(`/sessions/${sessionId}`, updates)
  return data
}

export async function deleteSession(sessionId: number): Promise<{ detail: string }> {
  const { data } = await apiClient.delete(`/sessions/${sessionId}`)
  return data
}

// ─── Chat Messages ────────────────────────────────────────────────────────────────

export async function addChatMessage(
  sessionId: number,
  msg: { role: string; content: string; status?: string; status_label?: string }
): Promise<ChatMessage> {
  const { data } = await apiClient.post(`/sessions/${sessionId}/messages`, msg)
  return data
}

export async function getChatMessages(sessionId: number): Promise<ChatMessage[]> {
  const { data } = await apiClient.get(`/sessions/${sessionId}/messages`)
  return data
}

// ─── Prompt Templates ─────────────────────────────────────────────────────────────

export async function listPromptTemplates(category?: string): Promise<PromptTemplate[]> {
  const { data } = await apiClient.get('/prompts', { params: category ? { category } : {} })
  return data
}

export async function listPromptCategories(): Promise<string[]> {
  const { data } = await apiClient.get('/prompts/categories')
  return data
}

export async function createPromptTemplate(
  template: Omit<PromptTemplate, 'id' | 'created_at'>
): Promise<PromptTemplate> {
  const { data } = await apiClient.post('/prompts', template)
  return data
}

export async function updatePromptTemplate(
  id: number,
  template: Partial<PromptTemplate>
): Promise<PromptTemplate> {
  const { data } = await apiClient.put(`/prompts/${id}`, template)
  return data
}

export async function deletePromptTemplate(id: number): Promise<{ detail: string }> {
  const { data } = await apiClient.delete(`/prompts/${id}`)
  return data
}

// ─── LLM Analysis SSE ─────────────────────────────────────────────────────────────

export function streamAnalysis(
  sessionId: number,
  message: string,
  fieldDefinitions: FieldDefinition[],
  fileId: number | null,
  onEvent: (event: string, data: string) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void
): AbortController {
  const controller = new AbortController()

  const params = new URLSearchParams({
    session_id: String(sessionId),
    message: message,
  })
  if (fileId) {
    params.set('file_id', String(fileId))
  }

  const url = `/api/v1/analyze/stream?${params.toString()}`

  fetch(url, {
    signal: controller.signal,
    headers: {
      'X-Field-Definitions': JSON.stringify(fieldDefinitions),
    },
  })
    .then(async (response) => {
      if (!response.ok) {
        const text = await response.text()
        throw new Error(`HTTP ${response.status}: ${text || response.statusText}`)
      }
      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6)
            onEvent(currentEvent, data)
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err)
      }
    })
    .finally(() => {
      onComplete?.()
    })

  return controller
}

// ─── Report Export ────────────────────────────────────────────────────────────────

export async function downloadReport(
  sessionId: number,
  format: 'word' | 'pdf' = 'word',
  fileId?: number
): Promise<void> {
  const params = new URLSearchParams({ format })
  if (fileId) params.set('file_id', String(fileId))

  const response = await fetch(`/api/v1/analyze/${sessionId}/report?${params.toString()}`)
  if (!response.ok) throw new Error('下载失败')

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const ext = format === 'word' ? 'docx' : 'pdf'
  const a = document.createElement('a')
  a.href = url
  a.download = `统计报告_${sessionId}.${ext}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

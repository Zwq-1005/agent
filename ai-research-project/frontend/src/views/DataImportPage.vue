<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { uploadFile, createSession, saveFieldDefinitions, type FieldDefinition, type PreviewData } from '@/api/analysis'
import { useAnalysisStore } from '@/stores/analysis'
import DataPreviewTable from '@/components/DataPreviewTable.vue'

const router = useRouter()
const message = useMessage()
const store = useAnalysisStore()

const uploading = ref(false)
const previewData = ref<PreviewData | null>(null)
const fields = ref<FieldDefinition[]>([])
const fieldsApplied = ref(false)
const fieldValidationErrors = ref<string[]>([])

const FIELD_TYPES = [
  { label: '数值型 (numeric)', value: 'numeric' },
  { label: '分类变量 (categorical)', value: 'categorical' },
  { label: '等级变量 (ordinal)', value: 'ordinal' },
  { label: '日期时间 (datetime)', value: 'datetime' },
  { label: '文本 (text)', value: 'text' },
  { label: 'ID/编号 (id)', value: 'id' },
]

const CATEGORICAL_TYPES: string[] = ['categorical', 'ordinal']

const fileSizeLimitMB = computed(() => store.getFileSizeLimit() / (1024 * 1024))

function inferFieldType(colName: string, sampleValues: unknown[]): FieldDefinition['field_type'] {
  const name = colName.toLowerCase()
  if (/^(id|编号|序号|patient_id|subject_id|住院号|病历号)$/i.test(name)) return 'id'
  if (/日期|时间|date|time|出生|入院|出院|手术/.test(name)) return 'datetime'
  const nonNull = sampleValues.filter(v => v !== null && v !== '' && v !== undefined)
  if (nonNull.length > 0) {
    const allNumeric = nonNull.every(v => !isNaN(Number(v)))
    if (allNumeric) {
      const allInts = nonNull.every(v => Number(v) === Math.floor(Number(v)))
      const uniqueVals = new Set(nonNull.map(v => Number(v)))
      if (allInts && uniqueVals.size <= 10) return 'ordinal'
      return 'numeric'
    }
  }
  return 'categorical'
}

async function handleUpload(options: { file: any; onFinish: Function; onError: Function }) {
  uploading.value = true
  fieldsApplied.value = false
  fieldValidationErrors.value = []
  try {
    const result = await uploadFile(options.file.file!, undefined, store.getFileSizeLimit())
    previewData.value = result
    store.setFileId(result.file_id)
    store.setCurrentStep(1)

    fields.value = result.columns.map((col) => ({
      original_name: col,
      display_name: col,
      field_type: inferFieldType(col, result.preview_rows.map(r => r[col])),
      unit: '',
      description: '',
      levels: '',
    }))

    const session = await createSession(`医学统计 - ${result.filename}`)
    store.setSessionId(session.id)

    message.success(`文件 "${result.filename}" 上传成功！请定义字段后再进行分析。`)
    options.onFinish()
  } catch (err: any) {
    const msg = err.response?.data?.detail || err.message || '上传失败'
    message.error(msg)
    options.onError?.()
  } finally {
    uploading.value = false
  }
}

function validateFields(): string[] {
  const errors: string[] = []
  const seenNames = new Set<string>()

  fields.value.forEach((f, idx) => {
    if (!f.display_name.trim()) {
      errors.push(`第 ${idx + 1} 列 "${f.original_name}" 的显示名称不能为空`)
    }
    if (seenNames.has(f.display_name.trim())) {
      errors.push(`显示名称 "${f.display_name}" 重复`)
    }
    seenNames.add(f.display_name.trim())

    if (CATEGORICAL_TYPES.includes(f.field_type) && !f.levels?.trim()) {
      errors.push(`分类变量 "${f.display_name || f.original_name}" 需要填写水平标签（如：男,女）`)
    }
  })
  return errors
}

async function applyFieldDefinitions() {
  const errors = validateFields()
  fieldValidationErrors.value = errors
  if (errors.length > 0) {
    message.error(`字段定义有 ${errors.length} 个问题，请修正后再应用`)
    return
  }

  if (!store.fileId) return
  try {
    await saveFieldDefinitions(store.fileId, fields.value)
    store.setFieldDefinitions(fields.value)
    fieldsApplied.value = true
    store.setCurrentStep(2)
    message.success('字段定义已应用！')

    setTimeout(() => {
      router.push('/clean')
    }, 1000)
  } catch (err: any) {
    message.error('保存字段定义失败：' + (err.message || '未知错误'))
  }
}

function goToClean() {
  if (fieldsApplied.value) {
    router.push('/clean')
  } else {
    message.warning('请先定义字段并点击"应用更改"')
  }
}
</script>

<template>
  <div class="import-page">
    <div class="import-inner">
      <div class="page-header">
        <div>
          <h1 class="page-title">步骤 1：数据导入和清洗</h1>
          <p class="page-desc">上传医学数据文件，定义每个字段的类型和标签，点击"应用更改"后生效</p>
        </div>
        <div class="tier-badge">
          <n-tag :type="store.vipTier === 'vip' ? 'success' : 'default'" round>
            {{ store.vipTier === 'vip' ? 'VIP 版 · 最大 20MB' : '基础版 · 最大 1MB' }}
          </n-tag>
        </div>
      </div>

      <!-- Upload Area -->
      <div v-if="!previewData" class="upload-section">
        <n-upload
          :max="1"
          accept=".csv,.xlsx,.xls,.json,.sav,.dta"
          :show-file-list="true"
          :custom-request="handleUpload"
          directory-dnd
        >
          <n-upload-dragger>
            <div class="upload-dragger-content">
              <n-icon size="48" color="#63e2b7">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </n-icon>
              <p class="upload-text">点击或拖拽医学数据文件到此区域上传</p>
              <p class="upload-hint">
                支持 CSV、Excel (.xlsx/.xls)、JSON、SPSS (.sav)、Stata (.dta) 格式
                <br/>限制大小：{{ fileSizeLimitMB }}MB
              </p>
              <n-tag type="warning" size="small" style="margin-top: 8px">
                ⚠ 请先完成"数据导入和清洗"步骤，定义字段后再进行分析
              </n-tag>
            </div>
          </n-upload-dragger>
        </n-upload>
      </div>

      <!-- Loading -->
      <div v-if="uploading" class="loading-section">
        <n-spin size="medium" />
        <p>正在解析文件...</p>
      </div>

      <!-- Preview + Field Definition -->
      <div v-if="previewData && !uploading" class="preview-section">
        <n-divider />

        <n-steps :current="fieldsApplied ? 2 : 1" style="margin-bottom: 24px">
          <n-step title="上传数据" description="文件已上传" />
          <n-step title="定义字段" description="设置类型和标签" />
          <n-step title="数据清洗" description="检测与清洗数据" />
        </n-steps>

        <!-- Field Definition Editor -->
        <div class="field-editor-card">
          <div class="card-header">
            <h2>
              <n-icon size="20" color="#63e2b7">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </n-icon>
              字段定义编辑器
              <n-tag v-if="fieldsApplied" type="success" size="small" round>已应用 ✓</n-tag>
              <n-tag v-else type="warning" size="small" round>待应用</n-tag>
            </h2>
            <p class="card-desc">为每个字段设置显示名称、数据类型、单位等元数据。带 <span style="color: #e04242">*</span> 的为必填项。</p>
          </div>

          <div v-if="fieldValidationErrors.length > 0" style="margin-bottom: 16px">
            <n-alert v-for="(err, idx) in fieldValidationErrors" :key="idx" type="error" style="margin-bottom: 6px">
              {{ err }}
            </n-alert>
          </div>

          <div class="fields-table-wrapper">
            <table class="fields-table">
              <thead>
                <tr>
                  <th style="width: 30px">#</th>
                  <th style="width: 140px">原始列名</th>
                  <th style="width: 160px">显示名称 <span class="required">*</span></th>
                  <th style="width: 150px">数据类型 <span class="required">*</span></th>
                  <th style="width: 80px">单位</th>
                  <th style="width: 180px">水平标签<br/><small>(分类变量必填)</small></th>
                  <th style="min-width: 160px">描述</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(field, idx) in fields" :key="field.original_name">
                  <td class="row-num">{{ idx + 1 }}</td>
                  <td><n-tag type="info" size="small">{{ field.original_name }}</n-tag></td>
                  <td>
                    <n-input
                      v-model:value="field.display_name"
                      size="small"
                      placeholder="中文显示名"
                      :status="!field.display_name.trim() ? 'error' : undefined"
                    />
                  </td>
                  <td>
                    <n-select v-model:value="field.field_type" :options="FIELD_TYPES" size="small" />
                  </td>
                  <td>
                    <n-input v-model:value="field.unit" size="small" placeholder="如: mg/dL" />
                  </td>
                  <td>
                    <n-input
                      v-model:value="field.levels"
                      size="small"
                      :placeholder="CATEGORICAL_TYPES.includes(field.field_type) ? '如: 男,女 或 轻度,中度,重度' : '非分类变量无需填写'"
                      :disabled="!CATEGORICAL_TYPES.includes(field.field_type)"
                      :status="CATEGORICAL_TYPES.includes(field.field_type) && !field.levels?.trim() ? 'warning' : undefined"
                    />
                  </td>
                  <td>
                    <n-input v-model:value="field.description" size="small" placeholder="字段含义说明" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="field-actions">
            <n-button type="primary" size="large" :disabled="fieldsApplied" @click="applyFieldDefinitions">
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </n-icon>
              </template>
              应用更改
            </n-button>
            <n-button v-if="fieldsApplied" type="success" size="large" @click="goToClean">
              前往数据清洗 →
            </n-button>
          </div>
        </div>

        <!-- Data Preview -->
        <n-divider />
        <div class="preview-toolbar">
          <div>
            <h2 class="preview-title">{{ previewData.filename }}</h2>
            <n-space>
              <n-tag type="info" size="small" round>共 {{ previewData.total_rows }} 行</n-tag>
              <n-tag type="info" size="small" round>{{ previewData.columns.length }} 列</n-tag>
            </n-space>
          </div>
        </div>
        <DataPreviewTable :columns="previewData.columns" :rows="previewData.preview_rows" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.import-page { min-height: 100vh; padding: 32px 24px 60px; }
.import-inner { max-width: 1200px; margin: 0 auto; }

.page-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
}

.page-title { font-size: 26px; font-weight: 700; color: #e8edf2; margin-bottom: 6px; }
.page-desc { font-size: 14px; color: #7d8692; }

.upload-section { margin-bottom: 24px; }

.upload-dragger-content {
  padding: 40px 20px;
  display: flex; flex-direction: column; align-items: center; gap: 12px;
}

.upload-text { font-size: 16px; color: #c0c7d0; font-weight: 500; }
.upload-hint { font-size: 13px; color: #5c6672; text-align: center; line-height: 1.6; }

.loading-section {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 40px; color: #7d8692;
}

.field-editor-card {
  background: #1a1f26;
  border: 1px solid rgba(99,226,183,0.15);
  border-radius: 14px;
  padding: 28px;
  margin-bottom: 20px;
}

.card-header h2 {
  font-size: 18px; font-weight: 600; color: #e0e4e9;
  display: flex; align-items: center; gap: 8px; margin-bottom: 4px;
}

.card-desc { font-size: 13px; color: #7d8692; margin-bottom: 16px; }
.required { color: #e04242; }

.fields-table-wrapper {
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}

.fields-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.fields-table th {
  text-align: left; padding: 10px 8px;
  background: rgba(99,226,183,0.08);
  color: #63e2b7; font-weight: 600; white-space: nowrap;
  position: sticky; top: 0; z-index: 2;
}

.fields-table th small { font-weight: 400; color: #7d8692; }
.fields-table td {
  padding: 6px 8px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  vertical-align: middle;
}

.row-num { color: #5c6672; font-weight: 600; text-align: center; }

.field-actions { margin-top: 20px; display: flex; gap: 12px; align-items: center; }

.preview-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; gap: 16px; flex-wrap: wrap;
}

.preview-title { font-size: 17px; font-weight: 600; color: #e0e4e9; margin-bottom: 4px; }
</style>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  getQualityReport,
  cleanData,
  getFilePreview,
  type QualityReport,
  type CleaningResult,
  type PreviewData,
} from '@/api/analysis'
import { useAnalysisStore } from '@/stores/analysis'
import DataPreviewTable from '@/components/DataPreviewTable.vue'

const router = useRouter()
const message = useMessage()
const store = useAnalysisStore()

const qualityReport = ref<QualityReport | null>(null)
const previewData = ref<PreviewData | null>(null)
const loading = ref(false)
const cleaning = ref(false)
const cleanResult = ref<CleaningResult | null>(null)

// Cleaning options
const dropDuplicates = ref(false)
const fillNumeric = ref<string | null>(null)
const fillCategorical = ref<string | null>(null)
const removeOutliers = ref(false)
const outlierColumns = ref<string[]>([])

const hasDataQualityIssues = computed(() => {
  if (!qualityReport.value) return false
  return (
    qualityReport.value.duplicate_rows > 0 ||
    qualityReport.value.total_missing > 0 ||
    qualityReport.value.columns.some(c => (c.outlier_count || 0) > 0)
  )
})

const numericColumns = computed(() => {
  if (!qualityReport.value) return []
  return qualityReport.value.columns
    .filter(c => c.min !== undefined)
    .map(c => c.column)
})

onMounted(async () => {
  if (!store.fileId) {
    router.replace('/import')
    return
  }

  loading.value = true
  try {
    const [quality, preview] = await Promise.all([
      getQualityReport(store.fileId),
      getFilePreview(store.fileId),
    ])
    qualityReport.value = quality
    previewData.value = preview

    if (quality.duplicate_rows > 0) dropDuplicates.value = true
    if (quality.total_missing > 0) {
      fillNumeric.value = 'median'
      fillCategorical.value = 'mode'
    }
  } catch (err: any) {
    message.error('获取数据质量报告失败：' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
})

async function handleClean() {
  if (!store.fileId) return

  cleaning.value = true
  try {
    const result = await cleanData({
      file_id: store.fileId,
      drop_duplicates: dropDuplicates.value,
      fill_numeric: fillNumeric.value,
      fill_categorical: fillCategorical.value,
      remove_outliers: removeOutliers.value,
      outlier_columns: removeOutliers.value ? outlierColumns.value : null,
    })

    cleanResult.value = result
    store.setCleanedFileId(result.file_id)
    message.success('数据清洗完成！')
  } catch (err: any) {
    message.error('数据清洗失败：' + (err.message || '未知错误'))
  } finally {
    cleaning.value = false
  }
}

function goToPrompts() {
  router.push('/prompts')
}

function goToWorksbench() {
  router.push('/worksbench')
}

function skipCleaning() {
  message.info('跳过数据清洗，直接使用原始数据')
  router.push('/prompts')
}
</script>

<template>
  <div class="clean-page">
    <div class="clean-inner">
      <div class="page-header">
        <div>
          <h1 class="page-title">步骤 2：数据清洗与预处理</h1>
          <p class="page-desc">检测数据质量问题并进行清洗，确保后续分析结果的准确性</p>
        </div>
        <n-space>
          <n-button @click="skipCleaning">跳过清洗 →</n-button>
        </n-space>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-section">
        <n-spin size="medium" />
        <p>正在生成数据质量报告...</p>
      </div>

      <!-- Quality Report -->
      <div v-if="qualityReport && !loading" class="quality-section">
        <n-steps :current="cleanResult ? 3 : 2" style="margin-bottom: 24px">
          <n-step title="上传数据" description="文件已上传" />
          <n-step title="质量检测" description="检测数据问题" />
          <n-step title="数据清洗" description="处理缺失值和异常值" />
          <n-step title="开始分析" description="前往分析工作台" />
        </n-steps>

        <!-- Quality Summary Cards -->
        <div class="quality-summary">
          <n-card size="small" :class="qualityReport.total_missing > 0 ? 'card-warning' : 'card-ok'">
            <n-statistic label="缺失值" :value="qualityReport.missing_pct + '%'">
              <template #suffix>{{ qualityReport.total_missing }} 个</template>
            </n-statistic>
          </n-card>
          <n-card size="small" :class="qualityReport.duplicate_rows > 0 ? 'card-warning' : 'card-ok'">
            <n-statistic label="重复行" :value="qualityReport.duplicate_pct + '%'">
              <template #suffix>{{ qualityReport.duplicate_rows }} 行</template>
            </n-statistic>
          </n-card>
          <n-card size="small" class="card-info">
            <n-statistic label="数据规模" :value="String(qualityReport.total_rows)">
              <template #suffix>行 × {{ qualityReport.total_columns }} 列</template>
            </n-statistic>
          </n-card>
          <n-card size="small" class="card-info">
            <n-statistic
              label="异常值(列)"
              :value="String(qualityReport.columns.filter(c => (c.outlier_count || 0) > 0).length)"
            >
              <template #suffix>列含异常值</template>
            </n-statistic>
          </n-card>
        </div>

        <!-- Per-column Quality -->
        <div class="column-quality">
          <h3>各列数据质量</h3>
          <n-data-table
            :columns="[
              { title: '列名', key: 'column', width: 150 },
              { title: '类型', key: 'dtype', width: 80 },
              { title: '缺失值', key: 'missing', width: 120 },
              { title: '异常值', key: 'outliers', width: 100 },
            ]"
            :data="qualityReport.columns.map(c => ({
              column: c.column,
              dtype: c.dtype,
              missing: `${c.missing_count} (${c.missing_pct}%)`,
              outliers: c.outlier_count ? `${c.outlier_count} (${c.outlier_pct}%)` : '无',
            }))"
            size="small"
            :bordered="true"
            max-height="300"
          />
        </div>

        <!-- Cleaning Controls -->
        <div class="cleaning-card">
          <div class="card-header">
            <h2>
              <n-icon size="20" color="#63e2b7">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="4 7 10 13 20 3" />
                  <polyline points="20 3 20 9" />
                  <line x1="20" y1="3" x2="14" y2="9" />
                </svg>
              </n-icon>
              数据清洗操作
            </h2>
          </div>

          <n-space vertical size="medium">
            <n-checkbox v-model:checked="dropDuplicates">
              删除重复行 ({{ qualityReport.duplicate_rows }} 行)
            </n-checkbox>

            <div class="cleaning-option">
              <span class="option-label">数值型缺失值填充策略：</span>
              <n-radio-group v-model:value="fillNumeric">
                <n-radio value="">不填充</n-radio>
                <n-radio value="mean">均值填充</n-radio>
                <n-radio value="median">中位数填充</n-radio>
              </n-radio-group>
            </div>

            <div class="cleaning-option">
              <span class="option-label">分类型缺失值填充策略：</span>
              <n-radio-group v-model:value="fillCategorical">
                <n-radio value="">不填充</n-radio>
                <n-radio value="mode">众数填充</n-radio>
                <n-radio value="missing_category">标记为"缺失"</n-radio>
              </n-radio-group>
            </div>

            <n-checkbox v-model:checked="removeOutliers">
              删除含异常值的行（IQR 法）
            </n-checkbox>

            <div v-if="removeOutliers" class="cleaning-option">
              <span class="option-label">检测异常值的列：</span>
              <n-select
                v-model:value="outlierColumns"
                :options="numericColumns.map(c => ({ label: c, value: c }))"
                multiple
                placeholder="选择列（不选则检测全部数值列）"
                style="max-width: 500px"
              />
            </div>
          </n-space>

          <div class="cleaning-actions">
            <n-button
              type="primary"
              size="large"
              :loading="cleaning"
              :disabled="!hasDataQualityIssues && !dropDuplicates && !fillNumeric && !fillCategorical && !removeOutliers"
              @click="handleClean"
            >
              <template #icon>
                <n-icon>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="4 7 10 13 20 3" />
                  </svg>
                </n-icon>
              </template>
              执行清洗
            </n-button>
          </div>

          <!-- Cleaning Result -->
          <div v-if="cleanResult" class="clean-result">
            <n-alert type="success" title="清洗完成">
              <p>清洗前: {{ cleanResult.cleaning_summary.rows_before }} 行 → 清洗后: {{ cleanResult.cleaning_summary.rows_after }} 行 (删除 {{ cleanResult.cleaning_summary.total_removed }} 行)</p>
              <ul>
                <li v-for="(action, idx) in cleanResult.cleaning_summary.actions" :key="idx">
                  {{ action.message }}
                </li>
              </ul>
            </n-alert>
            <n-space style="margin-top: 16px">
              <n-button type="success" @click="goToPrompts">前往 Prompt 模板 →</n-button>
              <n-button type="primary" @click="goToWorksbench">直接开始分析</n-button>
            </n-space>
          </div>
        </div>

        <!-- Data preview -->
        <n-divider />
        <div v-if="previewData" class="preview-toolbar">
          <div>
            <h2>数据预览</h2>
            <n-space>
              <n-tag type="info" size="small" round>{{ previewData.total_rows }} 行</n-tag>
              <n-tag type="info" size="small" round>{{ previewData.columns.length }} 列</n-tag>
            </n-space>
          </div>
        </div>
        <DataPreviewTable
          v-if="previewData"
          :columns="previewData.columns"
          :rows="previewData.preview_rows"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.clean-page { min-height: 100vh; padding: 32px 24px 60px; }
.clean-inner { max-width: 1200px; margin: 0 auto; }

.page-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
}

.page-title { font-size: 26px; font-weight: 700; color: #e8edf2; margin-bottom: 6px; }
.page-desc { font-size: 14px; color: #7d8692; }

.loading-section {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 60px; color: #7d8692;
}

/* Quality Summary */
.quality-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .quality-summary { grid-template-columns: repeat(2, 1fr); }
}

.card-warning { border: 1px solid rgba(240, 147, 43, 0.3); }
.card-ok { border: 1px solid rgba(99, 226, 183, 0.15); }
.card-info { border: 1px solid rgba(99, 160, 226, 0.15); }

.column-quality {
  margin-bottom: 24px;
}

.column-quality h3 {
  font-size: 16px; font-weight: 600; color: #e8edf2; margin-bottom: 12px;
}

/* Cleaning Card */
.cleaning-card {
  background: #1a1f26;
  border: 1px solid rgba(99,226,183,0.15);
  border-radius: 14px;
  padding: 28px;
  margin-bottom: 20px;
}

.card-header h2 {
  font-size: 18px; font-weight: 600; color: #e0e4e9;
  display: flex; align-items: center; gap: 8px; margin-bottom: 16px;
}

.cleaning-option {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}

.option-label { font-size: 14px; color: #a0aab4; white-space: nowrap; }

.cleaning-actions { margin-top: 20px; }

.clean-result { margin-top: 16px; }

.clean-result p { font-size: 14px; color: #63e2b7; margin-bottom: 8px; }
.clean-result ul { padding-left: 20px; }
.clean-result li { font-size: 13px; color: #a0aab4; line-height: 1.6; }

.preview-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; gap: 16px; flex-wrap: wrap;
}

.preview-toolbar h2 { font-size: 17px; font-weight: 600; color: #e0e4e9; }
</style>

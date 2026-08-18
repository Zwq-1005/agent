<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  columns: string[]
  rows: Record<string, unknown>[]
  maxHeight?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxHeight: 400,
})

const tableColumns = computed(() =>
  props.columns.map((col) => ({
    title: col,
    key: col,
    ellipsis: { tooltip: true },
    width: Math.max(120, Math.min(200, 1200 / props.columns.length)),
  }))
)
</script>

<template>
  <div class="preview-table">
    <div class="preview-header">
      <h3>数据预览</h3>
      <n-tag type="info" size="small" round>
        共 {{ columns.length }} 列
      </n-tag>
    </div>
    <n-data-table
      :columns="tableColumns"
      :data="rows"
      :bordered="true"
      :single-line="false"
      size="small"
      striped
      :max-height="maxHeight"
      virtual-scroll
    />
  </div>
</template>

<style scoped>
.preview-table {
  width: 100%;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.preview-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e8edf2;
}
</style>

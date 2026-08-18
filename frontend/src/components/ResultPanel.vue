<script setup lang="ts">
import { computed } from 'vue'
import type { ResultItem } from '@/stores/analysis'

interface Props {
  results: ResultItem[]
}

const props = defineProps<Props>()

const hasResults = computed(() => props.results.length > 0)
</script>

<template>
  <div class="result-panel">
    <div class="result-header">
      <h3>结果</h3>
      <n-tag v-if="hasResults" type="success" size="small" round>
        {{ results.length }} 条结果
      </n-tag>
    </div>
    <div class="result-content">
      <div v-if="!hasResults" class="result-empty">
        <n-icon size="48" color="#666d78">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <line x1="3" y1="9" x2="21" y2="9" />
            <line x1="9" y1="21" x2="9" y2="9" />
          </svg>
        </n-icon>
        <p>分析结果将在此展示</p>
      </div>
      <div
        v-for="(item, idx) in results"
        :key="idx"
        class="result-item"
        :class="`type-${item.type}`"
      >
        <div v-if="item.title" class="result-item-title">{{ item.title }}</div>
        <!-- Text result -->
        <div v-if="item.type === 'text'" class="result-text">
          {{ item.content }}
        </div>
        <!-- Code result -->
        <div v-if="item.type === 'code'" class="result-code">
          <n-ellipsis expand-trigger="click" line-clamp="15" :tooltip="false">
            <pre><code>{{ item.content }}</code></pre>
          </n-ellipsis>
        </div>
        <!-- Table result -->
        <n-data-table
          v-if="item.type === 'table'"
          :columns="item.columns || []"
          :data="item.rows || []"
          :bordered="true"
          size="small"
          max-height="350"
        />
        <!-- Chart result (base64 image) -->
        <div v-if="item.type === 'chart'" class="result-chart">
          <img
            :src="`data:image/png;base64,${item.content}`"
            :alt="item.title || '图表'"
          />
        </div>
        <!-- Error result -->
        <n-alert v-if="item.type === 'error'" type="error" :title="item.title">
          {{ item.content }}
        </n-alert>
      </div>
    </div>
  </div>
</template>

<style scoped>
.result-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #12161c;
}

.result-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.result-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e8edf2;
}

.result-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666d78;
  gap: 12px;
}

.result-empty p {
  font-size: 14px;
}

.result-item {
  background: #1a1f26;
  border-radius: 10px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.result-item-title {
  font-size: 14px;
  font-weight: 600;
  color: #63e2b7;
  margin-bottom: 10px;
}

.result-text {
  font-size: 14px;
  line-height: 1.7;
  color: #d0d5dc;
  white-space: pre-wrap;
}

.result-code {
  font-size: 13px;
}

.result-code pre {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 6px;
  padding: 12px;
  overflow: auto;
  font-family: 'Fira Code', 'Cascadia Code', 'SF Mono', monospace;
}

.result-code code {
  color: #63e2b7;
}

.result-chart img {
  max-width: 100%;
  border-radius: 6px;
}
</style>

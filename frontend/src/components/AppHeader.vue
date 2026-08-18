<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed, ref } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'

const route = useRoute()
const router = useRouter()
const store = useAnalysisStore()

const currentPath = computed(() => route.path)

const menuItems = [
  { label: '首页', key: '/' },
  { label: '数据导入和清洗', key: '/import' },
  { label: 'Prompt模版', key: '/prompts' },
  { label: '统计分析', key: '/worksbench' },
]

const showMaintenanceNotice = ref(true)

function navigate(path: string) {
  router.push(path)
}

function dismissNotice() {
  showMaintenanceNotice.value = false
}
</script>

<template>
  <n-layout-header bordered class="app-header">
    <!-- Maintenance Banner -->
    <div v-if="showMaintenanceNotice" class="maintenance-banner">
      <n-icon size="16">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </n-icon>
      <span>服务器每日凌晨 4:00 - 4:10 重启维护，期间无法访问，请及时保存统计结果文档。</span>
      <n-button text size="tiny" @click="dismissNotice">✕</n-button>
    </div>

    <div class="header-inner">
      <div class="header-brand" @click="router.push('/')">
        <svg class="brand-icon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
        <span class="brand-text">医学统计AI助手</span>
      </div>
      <n-menu
        mode="horizontal"
        :value="currentPath"
        :options="menuItems"
        class="header-menu"
        @update:value="navigate"
      />
    </div>
  </n-layout-header>
</template>

<style scoped>
.app-header {
  background: rgba(16, 20, 24, 0.98);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid rgba(99, 226, 183, 0.1);
}

.maintenance-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(240, 147, 43, 0.15);
  color: #f0a04b;
  font-size: 12px;
  border-bottom: 1px solid rgba(240, 147, 43, 0.2);
}

.header-inner {
  max-width: 1500px;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  gap: 12px;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}

.brand-icon {
  color: #63e2b7;
  flex-shrink: 0;
}

.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: #e8edf2;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.header-menu {
  background: transparent !important;
}
</style>

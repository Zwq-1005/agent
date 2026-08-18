<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  listPromptTemplates,
  listPromptCategories,
  createPromptTemplate,
  updatePromptTemplate,
  deletePromptTemplate,
  type PromptTemplate,
} from '@/api/analysis'

const router = useRouter()
const message = useMessage()

async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try { document.execCommand('copy'); return true } catch { return false }
    finally { document.body.removeChild(textarea) }
  }
}

const templates = ref<PromptTemplate[]>([])
const categories = ref<string[]>([])
const selectedCategory = ref<string>('all')
const editingTemplate = ref<PromptTemplate | null>(null)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const copiedId = ref<number | null>(null)

const newTemplate = ref({
  name: '',
  category: '',
  description: '',
  content: '',
  is_default: false,
})

const categoryLabels: Record<string, string> = {
  descriptive: '描述性统计',
  comparison: '组间比较',
  categorical: '分类变量分析',
  regression: '回归分析',
  survival: '生存分析',
  correlation: '相关性分析',
  diagnosis: '诊断试验',
  cleaning: '数据清洗',
  custom: '自定义模板',
}

const filteredTemplates = computed(() => {
  if (selectedCategory.value === 'all') return templates.value
  return templates.value.filter(t => t.category === selectedCategory.value)
})

onMounted(async () => {
  try {
    const [data, cats] = await Promise.all([
      listPromptTemplates(),
      listPromptCategories(),
    ])
    templates.value = data
    categories.value = cats
  } catch {
    message.warning('无法连接后端，请确认服务已启动')
  }
})

function getCategoryLabel(cat: string): string {
  return categoryLabels[cat] || cat
}

async function handleCopy(content: string, id: number) {
  const ok = await copyText(content)
  if (ok) {
    copiedId.value = id
    message.success('Prompt 已复制到剪贴板！可前往分析工作台粘贴使用')
    setTimeout(() => { copiedId.value = null }, 2000)
  } else {
    message.error('复制失败，请手动复制')
  }
}

function handleEdit(template: PromptTemplate) {
  editingTemplate.value = { ...template }
  showEditModal.value = true
}

async function handleSaveEdit() {
  if (!editingTemplate.value) return
  try {
    const updated = await updatePromptTemplate(editingTemplate.value.id, editingTemplate.value)
    const idx = templates.value.findIndex(t => t.id === updated.id)
    if (idx >= 0) templates.value[idx] = updated
    showEditModal.value = false
    message.success('模板已更新')
  } catch {
    message.error('更新失败')
  }
}

async function handleDelete(id: number) {
  try {
    await deletePromptTemplate(id)
    templates.value = templates.value.filter(t => t.id !== id)
    message.success('模板已删除')
  } catch {
    message.error('删除失败')
  }
}

async function handleCreate() {
  try {
    const created = await createPromptTemplate(newTemplate.value)
    templates.value.push(created)
    showCreateModal.value = false
    newTemplate.value = { name: '', category: '', description: '', content: '', is_default: false }
    message.success('自定义模板已创建')
  } catch {
    message.error('创建失败')
  }
}

function goToWorksbench() {
  router.push('/worksbench')
}
</script>

<template>
  <div class="prompts-page">
    <div class="prompts-inner">
      <div class="page-header">
        <div>
          <h1 class="page-title">步骤 3：准备命令 Prompt 模版</h1>
          <p class="page-desc">套用和编辑医学统计常用 Prompt 模板，复制后粘贴到分析工作台的对话中</p>
        </div>
        <n-space>
          <n-button @click="showCreateModal = true">
            <template #icon>
              <n-icon><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></n-icon>
            </template>
            自定义模板
          </n-button>
          <n-button type="primary" @click="goToWorksbench">前往分析工作台 →</n-button>
        </n-space>
      </div>

      <!-- Category filter -->
      <n-scrollbar x-scrollable style="margin-bottom: 20px">
        <n-space>
          <n-tag
            :type="selectedCategory === 'all' ? 'success' : 'default'"
            checkable
            :checked="selectedCategory === 'all'"
            @update:checked="selectedCategory = 'all'"
          >
            全部模板
          </n-tag>
          <n-tag
            v-for="cat in categories"
            :key="cat"
            :type="selectedCategory === cat ? 'success' : 'default'"
            checkable
            :checked="selectedCategory === cat"
            @update:checked="selectedCategory = cat"
          >
            {{ getCategoryLabel(cat) }}
          </n-tag>
        </n-space>
      </n-scrollbar>

      <!-- Template list -->
      <div class="templates-grid">
        <div v-for="tpl in filteredTemplates" :key="tpl.id" class="template-card">
          <div class="template-header">
            <h3>{{ tpl.name }}</h3>
            <n-space>
              <n-tag size="tiny" :bordered="false">{{ getCategoryLabel(tpl.category) }}</n-tag>
              <n-tag v-if="tpl.is_default" type="info" size="tiny">系统</n-tag>
            </n-space>
          </div>
          <p class="template-desc">{{ tpl.description }}</p>
          <div class="template-preview">
            <pre>{{ tpl.content.substring(0, 300) }}{{ tpl.content.length > 300 ? '...' : '' }}</pre>
          </div>
          <div class="template-actions">
            <n-button
              :type="copiedId === tpl.id ? 'success' : 'primary'"
              size="small"
              round
              @click="handleCopy(tpl.content, tpl.id)"
            >
              <template #icon>
                <n-icon>
                  <svg v-if="copiedId === tpl.id" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                  </svg>
                </n-icon>
              </template>
              {{ copiedId === tpl.id ? '已复制 ✓' : '复制 Prompt' }}
            </n-button>
            <n-space>
              <n-button text size="small" @click="handleEdit(tpl)">编辑</n-button>
              <n-popconfirm @positive-click="handleDelete(tpl.id)">
                <template #trigger>
                  <n-button text size="small" type="error">删除</n-button>
                </template>
                确认删除此模板？
              </n-popconfirm>
            </n-space>
          </div>
        </div>
      </div>

      <div v-if="filteredTemplates.length === 0" class="empty-state">
        <p>该分类下暂无模板</p>
      </div>
    </div>

    <!-- Create Modal -->
    <n-modal v-model:show="showCreateModal" title="创建自定义 Prompt 模板" style="width: 700px">
      <div class="modal-form">
        <n-form-item label="模板名称">
          <n-input v-model:value="newTemplate.name" placeholder="如：ROC曲线分析" />
        </n-form-item>
        <n-form-item label="分类">
          <n-input v-model:value="newTemplate.category" placeholder="如：diagnosis（诊断试验）" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="newTemplate.description" placeholder="模板用途简介" />
        </n-form-item>
        <n-form-item label="Prompt 内容">
          <n-input v-model:value="newTemplate.content" type="textarea" :rows="10" placeholder="编写统计分析 Prompt..." />
        </n-form-item>
        <n-button type="primary" block @click="handleCreate">创建模板</n-button>
      </div>
    </n-modal>

    <!-- Edit Modal -->
    <n-modal v-model:show="showEditModal" title="编辑 Prompt 模板" style="width: 700px">
      <div v-if="editingTemplate" class="modal-form">
        <n-form-item label="模板名称">
          <n-input v-model:value="editingTemplate.name" />
        </n-form-item>
        <n-form-item label="分类">
          <n-input v-model:value="editingTemplate.category" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="editingTemplate.description" />
        </n-form-item>
        <n-form-item label="Prompt 内容">
          <n-input v-model:value="editingTemplate.content" type="textarea" :rows="12" />
        </n-form-item>
        <n-button type="primary" block @click="handleSaveEdit">保存修改</n-button>
      </div>
    </n-modal>
  </div>
</template>

<style scoped>
.prompts-page { min-height: 100vh; padding: 32px 24px 60px; }
.prompts-inner { max-width: 1300px; margin: 0 auto; }

.page-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
}

.page-title { font-size: 26px; font-weight: 700; color: #e8edf2; margin-bottom: 6px; }
.page-desc { font-size: 14px; color: #7d8692; }

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.template-card {
  background: #1a1f26;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s;
}

.template-card:hover { border-color: rgba(99, 226, 183, 0.2); }

.template-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px; flex-wrap: wrap; gap: 6px;
}

.template-header h3 { font-size: 15px; font-weight: 600; color: #e0e4e9; }

.template-desc { font-size: 13px; color: #7d8692; margin-bottom: 10px; line-height: 1.5; }

.template-preview {
  flex: 1;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  max-height: 160px;
  overflow-y: auto;
}

.template-preview pre {
  font-size: 12px; color: #a0aab4; white-space: pre-wrap; word-break: break-word;
  font-family: inherit; line-height: 1.6;
}

.template-actions {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  flex-wrap: wrap;
}

.empty-state { text-align: center; padding: 60px; color: #5c6672; }

.modal-form { padding: 16px 0; display: flex; flex-direction: column; gap: 12px; }

@media (max-width: 768px) {
  .templates-grid { grid-template-columns: 1fr; }
}
</style>

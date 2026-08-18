import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomePage.vue'),
    },
    {
      path: '/import',
      name: 'data-import',
      component: () => import('@/views/DataImportPage.vue'),
    },
    {
      path: '/clean',
      name: 'data-clean',
      component: () => import('@/views/DataCleanPage.vue'),
    },
    {
      path: '/prompts',
      name: 'prompt-templates',
      component: () => import('@/views/PromptTemplatesPage.vue'),
    },
    {
      path: '/worksbench',
      name: 'worksbench',
      component: () => import('@/views/AnalysisWorkbench.vue'),
    },
  ],
})

export default router

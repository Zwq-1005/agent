<script setup lang="ts">
import { darkTheme, zhCN, dateZhCN } from 'naive-ui'
import AppHeader from './components/AppHeader.vue'
</script>

<template>
  <n-config-provider :theme="darkTheme" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-notification-provider>
        <div class="app-container">
          <AppHeader />
          <main class="app-main">
            <RouterView />
          </main>
        </div>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--n-color-body, #101418);
}

.app-main {
  flex: 1;
  padding: 0;
}
</style>

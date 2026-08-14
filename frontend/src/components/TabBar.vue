<template>
  <div class="tab-bar">
    <div
      v-for="tab in tabs"
      :key="tab.path"
      class="tab-bar-item"
      :class="{ active: currentPath === tab.path }"
      @click="handleTabClick(tab.path)"
    >
      <span class="tab-icon">{{ tab.icon }}</span>
      <span>{{ tab.name }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { path: '/home', name: '首页', icon: '🏠' },
  { path: '/topics', name: '专题', icon: '📋' },
  { path: '/briefing', name: '简报', icon: '📰' },
  { path: '/leads', name: '线索', icon: '🎯' },
  { path: '/profile', name: '我的', icon: '👤' },
]

const currentPath = computed(() => {
  const path = route.path
  // 匹配一级路径
  for (const tab of tabs) {
    if (path.startsWith(tab.path)) {
      return tab.path
    }
  }
  return '/home'
})

function handleTabClick(path: string) {
  router.push(path)
}
</script>

<style lang="scss" scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  background-color: #fff;
  border-top: 1px solid #f0f0f0;
  padding-bottom: env(safe-area-inset-bottom);
  height: 60px;
}

.tab-bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6px 0;
  font-size: 10px;
  color: #8c8c8c;
  transition: color 0.2s;
  cursor: pointer;

  &.active {
    color: #1a56db;
    font-weight: 600;
  }

  .tab-icon {
    font-size: 20px;
    margin-bottom: 2px;
  }
}
</style>

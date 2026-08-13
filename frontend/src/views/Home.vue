<template>
  <div class="home-page page-container">
    <!-- 顶部Header -->
    <div class="page-header">
      <div class="header-top">
        <div>
          <div class="page-title">对公资讯聚合</div>
          <div class="page-subtitle">{{ todayStr }} · 最后更新 {{ stats?.last_updated || '—' }}</div>
        </div>
        <div class="header-actions">
          <span class="search-icon" @click="showSearch = true">🔍</span>
        </div>
      </div>

      <!-- 统计看板 -->
      <div class="stat-board" v-if="stats">
        <div class="stat-item">
          <div class="stat-number">{{ stats.today_new }}</div>
          <div class="stat-label">今日新增</div>
          <div class="stat-trend" :class="stats.today_new_trend >= 0 ? 'up' : 'down'">
            {{ stats.today_new_trend >= 0 ? '↑' : '↓' }} {{ Math.abs(stats.today_new_trend) }}%
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ stats.bidding_count }}</div>
          <div class="stat-label">招投标</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ stats.policy_count }}</div>
          <div class="stat-label">政策动态</div>
        </div>
        <div class="stat-item">
          <div class="stat-number high-value">{{ stats.high_value_count }}</div>
          <div class="stat-label">高价值</div>
        </div>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <div class="filter-tabs">
        <div
          v-for="tab in filterTabs"
          :key="tab.value"
          class="filter-tab"
          :class="{ active: activeFilter === tab.value }"
          @click="handleFilterChange(tab.value)"
        >
          {{ tab.label }}
        </div>
      </div>

      <!-- 业务分类筛选 -->
      <div class="category-filters">
        <div
          v-for="cat in businessCategories"
          :key="cat.code"
          class="category-chip"
          :class="{ active: selectedCategory === cat.code }"
          :style="selectedCategory === cat.code ? { backgroundColor: cat.color + '20', color: cat.color, borderColor: cat.color } : {}"
          @click="handleCategoryChange(cat.code)"
        >
          <span class="chip-icon">{{ cat.icon }}</span>
          {{ cat.name }}
        </div>
      </div>
    </div>

    <!-- 视图切换 -->
    <div class="view-toggle">
      <div
        class="toggle-btn"
        :class="{ active: viewMode === 'list' }"
        @click="viewMode = 'list'"
      >
        📋 列表
      </div>
      <div
        class="toggle-btn"
        :class="{ active: viewMode === 'map' }"
        @click="viewMode = 'map'"
      >
        🗺️ 地图
      </div>
    </div>

    <!-- 资讯列表 -->
    <div class="news-list" v-if="viewMode === 'list'">
      <div v-if="loading" class="loading-state">
        <van-loading type="spinner" color="#1a2942" />
        <span>加载中...</span>
      </div>

      <NewsCard
        v-for="item in newsList"
        :key="item.id"
        :news="item"
      />

      <div v-if="!loading && newsList.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <div class="empty-text">暂无资讯</div>
      </div>

      <div v-if="hasMore" class="load-more" @click="loadMore">
        <span v-if="!loadingMore">加载更多</span>
        <van-loading v-else type="spinner" size="20px" color="#1a2942" />
      </div>
    </div>

    <!-- 地图视图（占位） -->
    <div class="map-view" v-else>
      <div class="map-placeholder">
        <div class="map-icon">🗺️</div>
        <div class="map-text">地图热力视图</div>
        <div class="map-hint">接入高德地图后展示区域分布热力图</div>
      </div>
    </div>

    <!-- 悬浮按钮：线索上报 -->
    <div class="fab" @click="goToCreateLead">
      <span>+</span>
    </div>

    <!-- 底部TabBar -->
    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import TabBar from '@/components/TabBar.vue'
import NewsCard from '@/components/NewsCard.vue'
import { getNewsList, getNewsStats, type NewsItem, type NewsStats } from '@/api/news'
import { businessCategoryMap, formatDate } from '@/utils/format'

const router = useRouter()

const todayStr = formatDate(new Date(), 'YYYY年MM月DD日 dddd')

const stats = ref<NewsStats | null>(null)
const newsList = ref<NewsItem[]>([])
const loading = ref(true)
const loadingMore = ref(false)
const page = ref(1)
const pageSize = 20
const hasMore = ref(true)
const viewMode = ref<'list' | 'map'>('list')
const showSearch = ref(false)

const activeFilter = ref('all')
const selectedCategory = ref('')

const filterTabs = [
  { label: '全部', value: 'all' },
  { label: '招投标', value: 'bidding' },
  { label: '政策', value: 'policy' },
  { label: '企业', value: 'enterprise' },
]

const businessCategories = computed(() => {
  return Object.entries(businessCategoryMap).map(([code, info]) => ({
    code,
    name: info.name,
    icon: info.icon,
    color: info.color,
  }))
})

onMounted(() => {
  loadStats()
  loadNews()
})

async function loadStats() {
  try {
    const res = await getNewsStats()
    if (res.code === 0) {
      stats.value = res.data
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

async function loadNews() {
  loading.value = true
  page.value = 1
  hasMore.value = true

  try {
    const params: any = {
      page: page.value,
      page_size: pageSize,
      status: 'published',
      sort_by: 'publish_date',
      sort_order: 'desc',
    }

    if (activeFilter.value !== 'all') {
      params.info_type = activeFilter.value
    }

    if (selectedCategory.value) {
      params.business_category = selectedCategory.value
    }

    const res = await getNewsList(params)
    if (res.code === 0) {
      newsList.value = res.data || []
      hasMore.value = (res.total || 0) > pageSize
    }
  } catch (error) {
    console.error('加载资讯列表失败:', error)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return

  loadingMore.value = true
  page.value++

  try {
    const params: any = {
      page: page.value,
      page_size: pageSize,
      status: 'published',
      sort_by: 'publish_date',
      sort_order: 'desc',
    }

    if (activeFilter.value !== 'all') {
      params.info_type = activeFilter.value
    }

    if (selectedCategory.value) {
      params.business_category = selectedCategory.value
    }

    const res = await getNewsList(params)
    if (res.code === 0) {
      newsList.value = [...newsList.value, ...(res.data || [])]
      hasMore.value = newsList.value.length < (res.total || 0)
    }
  } catch (error) {
    console.error('加载更多失败:', error)
  } finally {
    loadingMore.value = false
  }
}

function handleFilterChange(value: string) {
  activeFilter.value = value
  loadNews()
}

function handleCategoryChange(code: string) {
  selectedCategory.value = selectedCategory.value === code ? '' : code
  loadNews()
}

function goToCreateLead() {
  router.push('/leads/create')
}
</script>

<style lang="scss" scoped>
.home-page {
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #1a2942 0%, #2c3e5a 100%);
  color: #fff;
  padding: 20px 16px 24px;
  padding-top: calc(20px + env(safe-area-inset-top));
  border-radius: 0 0 20px 20px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;

  .page-title {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .page-subtitle {
    font-size: 13px;
    opacity: 0.7;
  }

  .header-actions {
    .search-icon {
      font-size: 20px;
      cursor: pointer;
    }
  }
}

.stat-board {
  display: flex;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px 8px;
  backdrop-filter: blur(10px);
}

.stat-item {
  flex: 1;
  text-align: center;

  .stat-number {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 4px;

    &.high-value {
      color: #ffd700;
    }
  }

  .stat-label {
    font-size: 11px;
    opacity: 0.8;
    margin-bottom: 2px;
  }

  .stat-trend {
    font-size: 10px;

    &.up {
      color: #52c41a;
    }

    &.down {
      color: #ff4d4f;
    }
  }
}

.filter-section {
  background-color: #fff;
  padding: 12px 16px;
  margin: -12px 12px 0;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: relative;
  z-index: 10;
}

.filter-tabs {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.filter-tab {
  font-size: 14px;
  color: #8c8c8c;
  cursor: pointer;
  position: relative;
  padding-bottom: 4px;

  &.active {
    color: #1a2942;
    font-weight: 600;

    &::after {
      content: '';
      position: absolute;
      bottom: -13px;
      left: 50%;
      transform: translateX(-50%);
      width: 24px;
      height: 3px;
      background-color: #1a2942;
      border-radius: 2px;
    }
  }
}

.category-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  color: #595959;
  background-color: #f5f5f5;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;

  .chip-icon {
    font-size: 12px;
  }

  &.active {
    font-weight: 500;
  }
}

.view-toggle {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px 8px;
  gap: 8px;
}

.toggle-btn {
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  color: #8c8c8c;
  background-color: #fff;
  cursor: pointer;
  transition: all 0.2s;

  &.active {
    color: #1a2942;
    background-color: #e6f7ff;
    font-weight: 500;
  }
}

.news-list {
  padding: 0 12px 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  gap: 12px;
  color: #8c8c8c;
  font-size: 14px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;

  .empty-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }

  .empty-text {
    font-size: 14px;
    color: #8c8c8c;
  }
}

.load-more {
  text-align: center;
  padding: 16px;
  color: #8c8c8c;
  font-size: 14px;
  cursor: pointer;
}

.map-view {
  padding: 12px;
  min-height: 400px;
}

.map-placeholder {
  background-color: #fff;
  border-radius: 12px;
  padding: 60px 20px;
  text-align: center;

  .map-icon {
    font-size: 64px;
    margin-bottom: 16px;
  }

  .map-text {
    font-size: 18px;
    font-weight: 600;
    color: #262626;
    margin-bottom: 8px;
  }

  .map-hint {
    font-size: 13px;
    color: #8c8c8c;
  }
}

.fab {
  position: fixed;
  right: 16px;
  bottom: 80px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1a2942 0%, #2c3e5a 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(26, 41, 66, 0.4);
  z-index: 99;
  font-size: 28px;
  font-weight: 300;
  cursor: pointer;

  &:active {
    transform: scale(0.95);
  }
}
</style>

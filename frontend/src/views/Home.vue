<template>
  <div class="home-page">
    <!-- 顶部Header -->
    <header class="app-header">
      <div class="header-top">
        <div class="header-title">
          <span class="logo-icon">🏦</span>
          <div>
            <h1>对公资讯聚合</h1>
            <p class="header-sub">北京东部 · 商机洞察</p>
          </div>
        </div>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-num">{{ stats.total }}</span>
            <span class="stat-label">资讯</span>
          </div>
          <div class="stat-item high-value">
            <span class="stat-num">{{ stats.highValue }}</span>
            <span class="stat-label">高价值</span>
          </div>
        </div>
      </div>

      <!-- 5分类导航 -->
      <nav class="category-nav">
        <div
          v-for="cat in categoryTabs"
          :key="cat.value"
          class="cat-item"
          :class="{ active: activeCategory === cat.value }"
          @click="switchCategory(cat.value)"
        >
          <span class="cat-icon">{{ cat.icon }}</span>
          <span class="cat-label">{{ cat.label }}</span>
        </div>
      </nav>
    </header>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-scroll">
        <div
          class="filter-chip"
          :class="{ active: activeArea === 'all' }"
          @click="setArea('all')"
        >全部区域</div>
        <div
          v-for="area in areaOptions"
          :key="area.value"
          class="filter-chip"
          :class="{ active: activeArea === area.value }"
          @click="setArea(area.value)"
        >{{ area.label }}</div>
      </div>
      <div class="filter-actions">
        <div class="filter-btn" @click="showFilterPanel = !showFilterPanel">
          <span>⚙️ 筛选</span>
          <span v-if="hasActiveFilters" class="filter-dot"></span>
        </div>
        <div class="sort-btn" @click="toggleSort">
          {{ sortBy === 'quality_score' ? '🔥 热度' : '🕐 最新' }}
        </div>
      </div>
    </div>

    <!-- 时间筛选栏 -->
    <div class="time-filter-bar">
      <div class="time-scroll">
        <div
          class="time-chip"
          :class="{ active: timeRange === 'all' }"
          @click="setTimeRange('all')"
        >全部时间</div>
        <div
          class="time-chip"
          :class="{ active: timeRange === '7d' }"
          @click="setTimeRange('7d')"
        >近7天</div>
        <div
          class="time-chip"
          :class="{ active: timeRange === '1m' }"
          @click="setTimeRange('1m')"
        >近1月</div>
        <div
          class="time-chip"
          :class="{ active: timeRange === '3m' }"
          @click="setTimeRange('3m')"
        >近3月</div>
        <div
          class="time-chip"
          :class="{ active: timeRange === '6m' }"
          @click="setTimeRange('6m')"
        >近半年</div>
      </div>
    </div>

    <!-- 展开筛选面板 -->
    <div v-if="showFilterPanel" class="filter-panel">
      <div class="panel-section">
        <label class="panel-label">最低商机分</label>
        <div class="score-slider">
          <input type="range" min="0" max="100" step="10" v-model.number="minScore" @input="applyFilters" />
          <span class="score-value">{{ minScore }}分+</span>
        </div>
      </div>
      <div class="panel-section">
        <label class="panel-label">行业</label>
        <div class="industry-chips">
          <div
            class="industry-chip"
            :class="{ active: selectedIndustry === '' }"
            @click="setIndustry('')"
          >全部</div>
          <div
            v-for="ind in industryOptions"
            :key="ind.value"
            class="industry-chip"
            :class="{ active: selectedIndustry === ind.value }"
            @click="setIndustry(ind.value)"
          >{{ ind.label }}</div>
        </div>
      </div>
    </div>

    <!-- 今日商机摘要卡 -->
    <div class="summary-card">
      <div class="summary-item">
        <span class="summary-num">{{ stats.today }}</span>
        <span class="summary-label">今日新增</span>
      </div>
      <div class="summary-divider"></div>
      <div class="summary-item">
        <span class="summary-num high">{{ stats.highValue }}</span>
        <span class="summary-label">高价值</span>
      </div>
      <div class="summary-divider"></div>
      <div class="summary-item">
        <span class="summary-num bid">{{ bidCount }}</span>
        <span class="summary-label">可投标</span>
      </div>
      <div class="summary-divider"></div>
      <div class="summary-item">
        <span class="summary-num fin">{{ finCount }}</span>
        <span class="summary-label">融资需求</span>
      </div>
    </div>

    <!-- 高价值商机区（横向滑动） -->
    <div v-if="highValueNews.length > 0 && activeCategory === 'all' && !hasActiveFilters" class="high-value-section">
      <div class="section-header">
        <span class="section-icon">🔥</span>
        <span class="section-title">高价值商机</span>
        <span class="section-count">{{ highValueNews.length }}条</span>
      </div>
      <div class="hv-scroll">
        <div
          v-for="item in highValueNews.slice(0, 8)"
          :key="'hv-' + item.id"
          class="hv-card"
          @click="goDetail(item.id)"
        >
          <div class="hv-score">{{ item.quality_score }}</div>
          <div class="hv-content">
            <h3 class="hv-title">{{ item.title }}</h3>
            <div class="hv-meta">
              <span class="hv-source">{{ item.source_channel }}</span>
              <span class="hv-date">{{ formatDate(item.publish_date) }}</span>
            </div>
            <div class="hv-cat" :style="{ color: getCatColor(item.business_category) }">
              {{ getCatName(item.business_category) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 资讯列表 -->
    <div class="news-list">
      <div v-if="loading && newsList.length === 0" class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="newsList.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <p>暂无相关资讯</p>
        <p class="empty-hint">试试切换分类或调整筛选条件</p>
      </div>

      <template v-else>
        <NewsCard
          v-for="item in newsList"
          :key="item.id"
          :news="item"
          @click="goDetail(item.id)"
        />
      </template>

      <!-- 加载更多 -->
      <div v-if="newsList.length > 0" class="load-more">
        <div v-if="loading" class="loading-more">
          <div class="spinner small"></div>
          <span>加载中...</span>
        </div>
        <div v-else-if="hasMore" class="load-more-btn" @click="loadMore">
          加载更多
        </div>
        <div v-else class="no-more">— 已经到底了 —</div>
      </div>
    </div>

    <!-- 浮动按钮 -->
    <div class="fab" @click="scrollToTop">
      <span>↑</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import NewsCard from '../components/NewsCard.vue'
import { getNewsList, getNewsStats, type NewsItem, type NewsQueryParams } from '../api/news'
import { formatDate, businessCategoryMap } from '../utils/format'

const router = useRouter()

// 5个行动分类（v4）
const categoryTabs = [
  { value: 'all', label: '全部', icon: '📰' },
  { value: 'bid_action', label: '可投标', icon: '📑' },
  { value: 'fin_demand', label: '融资需求', icon: '💰' },
  { value: 'account_chance', label: '开户机会', icon: '🏦' },
  { value: 'park_project', label: '区域动态', icon: '🏗️' },
  { value: 'policy_ref', label: '政策', icon: '📋' },
]

// 区域选项（标准7类）
const areaOptions = [
  { value: 'chaoyang', label: '朝阳' },
  { value: 'dongcheng', label: '东城' },
  { value: 'tongzhou', label: '通州' },
  { value: 'yizhuang', label: '亦庄' },
  { value: 'beijing', label: '市级' },
  { value: 'national', label: '全国' },
]

// 行业选项（北京主导产业）
const industryOptions = [
  { value: 'finance', label: '金融' },
  { value: 'tech', label: '科技' },
  { value: 'digital_economy', label: '数字经济' },
  { value: 'advanced_manufacturing', label: '先进制造' },
  { value: 'medical_health', label: '医药健康' },
  { value: 'culture', label: '文化' },
  { value: 'business_service', label: '商务服务' },
]

// 状态
const newsList = ref<NewsItem[]>([])
const highValueNews = ref<NewsItem[]>([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 20

const activeCategory = ref('all')
const activeArea = ref('all')
const selectedIndustry = ref('')
const minScore = ref(0)
const timeRange = ref('all')
const sortBy = ref('publish_date')
const showFilterPanel = ref(false)

const stats = ref({ total: 0, highValue: 0, today: 0 })

// 行动分类计数
const bidCount = computed(() => newsList.value.filter(n => n.business_category === 'bid_action').length)
const finCount = computed(() => newsList.value.filter(n => n.business_category === 'fin_demand').length)

function getCatName(cat?: string): string {
  return businessCategoryMap[cat || '']?.name || cat || ''
}

function getCatColor(cat?: string): string {
  return businessCategoryMap[cat || '']?.color || '#999'
}

const hasActiveFilters = computed(() => {
  return activeArea.value !== 'all' || selectedIndustry.value !== '' || minScore.value > 0 || timeRange.value !== 'all'
})

function buildQueryParams(): NewsQueryParams {
  const params: NewsQueryParams = {
    page: page.value,
    page_size: pageSize,
    status: 'published',
    sort_by: sortBy.value,
    sort_order: 'desc',
  }
  if (activeCategory.value !== 'all') {
    params.business_category = activeCategory.value
  }
  if (activeArea.value !== 'all') {
    params.area_tags = activeArea.value
  }
  if (selectedIndustry.value) {
    params.industry_tags = selectedIndustry.value
  }
  if (minScore.value > 0) {
    params.min_quality_score = minScore.value
  }
  if (timeRange.value !== 'all') {
    params.date_range = timeRange.value
  }
  return params
}

async function loadNews(reset = false) {
  if (loading.value) return
  if (reset) {
    page.value = 1
    newsList.value = []
    hasMore.value = true
  }
  loading.value = true
  try {
    const params = buildQueryParams()
    const res = await getNewsList(params)
    const items = res.data || []
    if (reset) {
      newsList.value = items
    } else {
      // 去重
      const existingIds = new Set(newsList.value.map(n => n.id))
      const newItems = items.filter(n => !existingIds.has(n.id))
      newsList.value = [...newsList.value, ...newItems]
    }
    hasMore.value = items.length >= pageSize
  } catch (e) {
    console.error('加载资讯失败', e)
  } finally {
    loading.value = false
  }
}

async function loadHighValue() {
  try {
    const res = await getNewsList({
      page: 1,
      page_size: 10,
      status: 'published',
      min_quality_score: 80,
      sort_by: 'quality_score',
      sort_order: 'desc',
    })
    highValueNews.value = res.data || []
  } catch (e) {
    console.error('加载高价值资讯失败', e)
  }
}

async function loadStats() {
  try {
    const res = await getNewsStats()
    stats.value = {
      total: res.total || (res.policy_count || 0) + (res.bidding_count || 0) + (res.enterprise_count || 0),
      highValue: res.high_value_count || 0,
      today: res.today_new || 0,
    }
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

function switchCategory(cat: string) {
  activeCategory.value = cat
  loadNews(true)
}

function setArea(area: string) {
  activeArea.value = area
  loadNews(true)
}

function setIndustry(ind: string) {
  selectedIndustry.value = ind
  loadNews(true)
}

function setTimeRange(range: string) {
  timeRange.value = range
  loadNews(true)
}

function applyFilters() {
  loadNews(true)
}

function toggleSort() {
  sortBy.value = sortBy.value === 'publish_date' ? 'quality_score' : 'publish_date'
  loadNews(true)
}

function loadMore() {
  if (!hasMore.value || loading.value) return
  page.value++
  loadNews(false)
}

function goDetail(id: string) {
  router.push(`/news/${id}`)
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  loadNews(true)
  loadHighValue()
  loadStats()
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 80px;
}

/* Header */
.app-header {
  background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
  color: #fff;
  padding: 16px 16px 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 12px rgba(26, 86, 219, 0.15);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  font-size: 28px;
}

.header-title h1 {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.5px;
}

.header-sub {
  font-size: 11px;
  opacity: 0.8;
  margin: 2px 0 0;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 20px;
  font-weight: 700;
}

.stat-label {
  font-size: 10px;
  opacity: 0.75;
}

.stat-item.high-value .stat-num {
  color: #fbbf24;
}

/* 分类导航 */
.category-nav {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  padding-bottom: 10px;
  scrollbar-width: none;
}

.category-nav::-webkit-scrollbar {
  display: none;
}

.cat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 56px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.1);
}

.cat-item.active {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.cat-icon {
  font-size: 18px;
  margin-bottom: 2px;
}

.cat-label {
  font-size: 11px;
  white-space: nowrap;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #eef0f4;
  position: sticky;
  top: 108px;
  z-index: 99;
}

.filter-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  flex: 1;
  scrollbar-width: none;
}

.filter-scroll::-webkit-scrollbar {
  display: none;
}

.filter-chip {
  padding: 5px 12px;
  border-radius: 14px;
  font-size: 12px;
  color: #595959;
  background: #f0f2f5;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.filter-chip.active {
  background: #e6f0ff;
  color: #1a56db;
  font-weight: 600;
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: 8px;
  flex-shrink: 0;
}

.filter-btn, .sort-btn {
  padding: 5px 10px;
  border-radius: 14px;
  font-size: 12px;
  color: #595959;
  background: #f0f2f5;
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
  position: relative;
}

.filter-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1a56db;
  position: absolute;
  top: 2px;
  right: 2px;
}

/* 时间筛选栏 */
.time-filter-bar {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #eef0f4;
  position: sticky;
  top: 152px;
  z-index: 98;
}

.time-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  flex: 1;
  scrollbar-width: none;
}

.time-scroll::-webkit-scrollbar {
  display: none;
}

.time-chip {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  color: #8c8c8c;
  background: #f5f7fa;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.time-chip.active {
  background: #fff;
  color: #1a56db;
  border-color: #1a56db;
  font-weight: 600;
}

/* 筛选面板 */
.filter-panel {
  background: #fff;
  padding: 14px 16px;
  border-bottom: 1px solid #eef0f4;
}

.panel-section {
  margin-bottom: 12px;
}

.panel-section:last-child {
  margin-bottom: 0;
}

.panel-label {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 8px;
  display: block;
}

.score-slider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-slider input[type="range"] {
  flex: 1;
  accent-color: #1a56db;
}

.score-value {
  font-size: 13px;
  font-weight: 600;
  color: #1a56db;
  min-width: 50px;
}

.industry-chips, .time-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.industry-chip, .time-chip {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  color: #595959;
  background: #f0f2f5;
  cursor: pointer;
}

.industry-chip.active, .time-chip.active {
  background: #e6f0ff;
  color: #1a56db;
  font-weight: 600;
}

/* 今日商机摘要卡 */
.summary-card {
  margin: 0 16px 12px;
  background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
  border-radius: 14px;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 4px 12px rgba(26, 86, 219, 0.25);
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.summary-num {
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  line-height: 1;

  &.high { color: #fbbf24; }
  &.bid { color: #60a5fa; }
  &.fin { color: #f97316; }
}

.summary-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.75);
}

.summary-divider {
  width: 1px;
  height: 28px;
  background: rgba(255, 255, 255, 0.2);
}

/* 高价值区 */
.high-value-section {
  margin: 0 16px 12px;
  background: linear-gradient(135deg, #fff7ed 0%, #fef3c7 100%);
  border-radius: 14px;
  padding: 14px;
  border: 1px solid #fde68a;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.section-icon {
  font-size: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #92400e;
}

.section-count {
  font-size: 11px;
  color: #b45309;
  background: rgba(180, 83, 9, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: auto;
}

/* 横向滑动 */
.hv-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;

  &::-webkit-scrollbar {
    display: none;
  }
}

.hv-card {
  flex-shrink: 0;
  width: 220px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
  scroll-snap-align: start;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.hv-card:active {
  background: rgba(255, 255, 255, 1);
}

.hv-score {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hv-content {
  flex: 1;
  min-width: 0;
}

.hv-title {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.hv-meta {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.hv-cat {
  font-size: 11px;
  font-weight: 600;
}

/* 资讯列表 */
.news-list {
  padding: 12px 16px;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #8c8c8c;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-hint {
  font-size: 12px;
  color: #bfbfbf;
  margin-top: 4px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e6f0ff;
  border-top-color: #1a56db;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

.spinner.small {
  width: 16px;
  height: 16px;
  margin-bottom: 0;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.load-more {
  padding: 20px 0;
  text-align: center;
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #8c8c8c;
}

.load-more-btn {
  display: inline-block;
  padding: 8px 24px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 20px;
  font-size: 13px;
  color: #595959;
  cursor: pointer;
}

.no-more {
  font-size: 12px;
  color: #bfbfbf;
}

/* FAB */
.fab {
  position: fixed;
  right: 16px;
  bottom: 90px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1a56db, #1e40af);
  color: #fff;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(26, 86, 219, 0.3);
  cursor: pointer;
  z-index: 50;
  transition: transform 0.2s;
}

.fab:active {
  transform: scale(0.92);
}
</style>

<template>
  <div class="briefing-page page-container">
    <!-- 顶部Header -->
    <div class="page-header">
      <div class="page-title">每日简报</div>
      <div class="page-subtitle">{{ currentDateStr }}</div>
    </div>

    <!-- 日期选择 -->
    <div class="date-selector">
      <div class="date-nav" @click="prevDay">
        <span>←</span>
      </div>
      <div class="current-date">{{ formatDate(currentDate, 'MM月DD日 dddd') }}</div>
      <div class="date-nav" @click="nextDay">
        <span>→</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <van-loading type="spinner" color="#1a2942" />
      <span>加载中...</span>
    </div>

    <div v-else-if="briefing" class="briefing-content">
      <!-- 简报概览 -->
      <div class="briefing-overview">
        <div class="overview-item">
          <div class="overview-number">{{ briefing.total_count }}</div>
          <div class="overview-label">今日资讯</div>
        </div>
        <div class="overview-item">
          <div class="overview-number high-value">{{ briefing.content_json?.high_value_count || 0 }}</div>
          <div class="overview-label">高价值</div>
        </div>
        <div class="overview-item">
          <div class="overview-number">{{ categoryCount }}</div>
          <div class="overview-label">业务分类</div>
        </div>
      </div>

      <!-- 分类列表 -->
      <div class="category-list">
        <div
          v-for="category in briefing.content_json?.categories || []"
          :key="category.category_code"
          class="category-section"
        >
          <div class="category-header" @click="toggleCategory(category.category_code)">
            <span class="category-icon">{{ category.icon }}</span>
            <span class="category-name">{{ category.category_name }}</span>
            <span class="category-count">{{ category.count }}条</span>
            <span class="category-arrow" :class="{ expanded: expandedCategories.includes(category.category_code) }">
              ▼
            </span>
          </div>

          <div
            v-if="expandedCategories.includes(category.category_code)"
            class="category-items"
          >
            <div
              v-for="item in category.items"
              :key="item.id"
              class="briefing-item"
              @click="goToDetail(item.id)"
            >
              <div class="item-title ellipsis-2">{{ item.title }}</div>
              <div class="item-tip" v-if="item.business_tip">
                💡 {{ item.business_tip }}
              </div>
              <div class="item-footer">
                <span class="item-score" :style="{ color: getQualityScoreColor(item.quality_score) }">
                  {{ item.quality_score }}分
                </span>
                <span class="item-type">{{ item.info_type }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">📰</div>
      <div class="empty-text">当日暂无简报</div>
    </div>

    <!-- 底部TabBar -->
    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import TabBar from '@/components/TabBar.vue'
import { getBriefingByDate, type DailyBriefing } from '@/api/briefing'
import { formatDate, getQualityScoreColor } from '@/utils/format'

const router = useRouter()

const currentDate = ref(dayjs().format('YYYY-MM-DD'))
const briefing = ref<DailyBriefing | null>(null)
const loading = ref(true)
const expandedCategories = ref<string[]>([])

const currentDateStr = computed(() => {
  return formatDate(currentDate.value, 'YYYY年MM月DD日')
})

const categoryCount = computed(() => {
  return briefing.value?.content_json?.categories?.length || 0
})

onMounted(() => {
  loadBriefing()
})

async function loadBriefing() {
  loading.value = true
  try {
    const res = await getBriefingByDate(currentDate.value)
    if (res.code === 0) {
      briefing.value = res.data
      // 默认展开第一个分类
      if (res.data?.content_json?.categories?.length) {
        expandedCategories.value = [res.data.content_json.categories[0].category_code]
      }
    } else {
      briefing.value = null
    }
  } catch (error) {
    console.error('加载简报失败:', error)
    briefing.value = null
  } finally {
    loading.value = false
  }
}

function prevDay() {
  currentDate.value = dayjs(currentDate.value).subtract(1, 'day').format('YYYY-MM-DD')
  loadBriefing()
}

function nextDay() {
  const next = dayjs(currentDate.value).add(1, 'day')
  if (next.isAfter(dayjs(), 'day')) {
    return
  }
  currentDate.value = next.format('YYYY-MM-DD')
  loadBriefing()
}

function toggleCategory(code: string) {
  const index = expandedCategories.value.indexOf(code)
  if (index > -1) {
    expandedCategories.value.splice(index, 1)
  } else {
    expandedCategories.value.push(code)
  }
}

function goToDetail(id: string) {
  router.push(`/news/${id}`)
}
</script>

<style lang="scss" scoped>
.briefing-page {
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #1a2942 0%, #2c3e5a 100%);
  color: #fff;
  padding: 20px 16px 60px;
  padding-top: calc(20px + env(safe-area-inset-top));
  text-align: center;

  .page-title {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .page-subtitle {
    font-size: 13px;
    opacity: 0.7;
  }
}

.date-selector {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin: -40px 16px 16px;
  padding: 16px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  position: relative;
  z-index: 10;

  .date-nav {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f5f5f5;
    border-radius: 50%;
    cursor: pointer;
    font-size: 14px;
    color: #595959;
  }

  .current-date {
    font-size: 16px;
    font-weight: 600;
    color: #262626;
  }
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

.briefing-content {
  padding: 0 16px 20px;
}

.briefing-overview {
  display: flex;
  background-color: #fff;
  border-radius: 12px;
  padding: 20px 16px;
  margin-bottom: 12px;
}

.overview-item {
  flex: 1;
  text-align: center;

  .overview-number {
    font-size: 28px;
    font-weight: 700;
    color: #1a2942;
    margin-bottom: 4px;

    &.high-value {
      color: #f39c12;
    }
  }

  .overview-label {
    font-size: 12px;
    color: #8c8c8c;
  }
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-section {
  background-color: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.category-header {
  display: flex;
  align-items: center;
  padding: 16px;
  cursor: pointer;

  .category-icon {
    font-size: 20px;
    margin-right: 10px;
  }

  .category-name {
    flex: 1;
    font-size: 15px;
    font-weight: 600;
    color: #262626;
  }

  .category-count {
    font-size: 12px;
    color: #8c8c8c;
    margin-right: 8px;
  }

  .category-arrow {
    font-size: 10px;
    color: #bfbfbf;
    transition: transform 0.2s;

    &.expanded {
      transform: rotate(180deg);
    }
  }
}

.category-items {
  border-top: 1px solid #f0f0f0;
}

.briefing-item {
  padding: 14px 16px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background-color: #fafafa;
  }
}

.item-title {
  font-size: 14px;
  color: #262626;
  line-height: 1.5;
  margin-bottom: 8px;
}

.item-tip {
  font-size: 12px;
  color: #ad6800;
  background-color: #fffbe6;
  padding: 6px 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  line-height: 1.5;
}

.item-footer {
  display: flex;
  align-items: center;
  gap: 12px;

  .item-score {
    font-size: 12px;
    font-weight: 600;
  }

  .item-type {
    font-size: 11px;
    color: #bfbfbf;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 0;

  .empty-icon {
    font-size: 64px;
    margin-bottom: 16px;
  }

  .empty-text {
    font-size: 14px;
    color: #8c8c8c;
  }
}
</style>

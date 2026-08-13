<template>
  <div class="topic-detail-page">
    <!-- 顶部导航 -->
    <div class="nav-bar">
      <div class="nav-back" @click="goBack">
        <span>←</span>
      </div>
      <div class="nav-title">{{ topic?.title || '专题详情' }}</div>
      <div class="nav-actions"></div>
    </div>

    <!-- 专题封面 -->
    <div class="topic-cover" v-if="topic">
      <div class="cover-content">
        <h1 class="topic-title">{{ topic.title }}</h1>
        <p class="topic-desc" v-if="topic.description">{{ topic.description }}</p>
        <div class="topic-stats">
          <div class="stat">
            <span class="stat-num">{{ topic.total_count || 0 }}</span>
            <span class="stat-label">资讯</span>
          </div>
          <div class="stat">
            <span class="stat-num">{{ topic.month_new_count || 0 }}</span>
            <span class="stat-label">本月新增</span>
          </div>
          <div class="stat">
            <span class="stat-num high-value">{{ topic.high_value_count || 0 }}</span>
            <span class="stat-label">高价值</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 资讯列表 -->
    <div class="news-section">
      <div class="section-header">
        <span class="section-title">专题资讯</span>
        <span class="section-count">共 {{ total }} 条</span>
      </div>

      <div v-if="loading" class="loading-state">
        <van-loading type="spinner" color="#1a2942" />
        <span>加载中...</span>
      </div>

      <div v-else class="news-list">
        <NewsCard
          v-for="item in newsList"
          :key="item.id"
          :news="item"
        />

        <div v-if="newsList.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-text">暂无资讯</div>
        </div>

        <div v-if="hasMore" class="load-more" @click="loadMore">
          <span v-if="!loadingMore">加载更多</span>
          <van-loading v-else type="spinner" size="20px" color="#1a2942" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NewsCard from '@/components/NewsCard.vue'
import { getTopicNews, type NewsItem, type TopicInfo } from '@/api/news'

const route = useRoute()
const router = useRouter()

const topic = ref<TopicInfo | null>(null)
const newsList = ref<NewsItem[]>([])
const loading = ref(true)
const loadingMore = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const hasMore = ref(false)

onMounted(() => {
  loadTopicNews()
})

async function loadTopicNews() {
  const topicId = route.params.id as string
  if (!topicId) return

  loading.value = true
  page.value = 1

  try {
    const res = await getTopicNews(topicId, page.value, pageSize)
    if (res.code === 0) {
      newsList.value = res.data || []
      total.value = res.total || 0
      hasMore.value = total.value > pageSize
    }
  } catch (error) {
    console.error('加载专题资讯失败:', error)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return

  loadingMore.value = true
  page.value++

  try {
    const topicId = route.params.id as string
    const res = await getTopicNews(topicId, page.value, pageSize)
    if (res.code === 0) {
      // 按id去重，防止offset分页在数据插入时产生重复资讯
      const existingIds = new Set(newsList.value.map(n => n.id))
      const newItems = (res.data || []).filter(n => !existingIds.has(n.id))
      newsList.value = [...newsList.value, ...newItems]
      hasMore.value = newsList.value.length < (res.total || 0)
    }
  } catch (error) {
    console.error('加载更多失败:', error)
  } finally {
    loadingMore.value = false
  }
}

function goBack() {
  router.back()
}
</script>

<style lang="scss" scoped>
.topic-detail-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.nav-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top));
  background-color: rgba(26, 41, 66, 0.95);
  backdrop-filter: blur(10px);
  color: #fff;

  .nav-back {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    cursor: pointer;
  }

  .nav-title {
    font-size: 16px;
    font-weight: 600;
  }

  .nav-actions {
    width: 32px;
  }
}

.topic-cover {
  background: linear-gradient(135deg, #1a2942 0%, #2c3e5a 100%);
  color: #fff;
  padding: 20px 16px 30px;
  padding-top: calc(20px + env(safe-area-inset-top) + 44px);
  margin-top: -44px;
}

.cover-content {
  .topic-title {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 12px;
  }

  .topic-desc {
    font-size: 14px;
    opacity: 0.8;
    line-height: 1.6;
    margin-bottom: 20px;
  }
}

.topic-stats {
  display: flex;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px 8px;
  backdrop-filter: blur(10px);
}

.stat {
  flex: 1;
  text-align: center;

  .stat-num {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 4px;
    display: block;

    &.high-value {
      color: #ffd700;
    }
  }

  .stat-label {
    font-size: 11px;
    opacity: 0.8;
  }
}

.news-section {
  padding: 12px;
  margin-top: -16px;
  position: relative;
  z-index: 10;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px 12px;

  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #262626;
  }

  .section-count {
    font-size: 12px;
    color: #8c8c8c;
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

.news-list {
  display: flex;
  flex-direction: column;
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
</style>

<template>
  <div class="topics-page page-container">
    <!-- 顶部Header -->
    <div class="page-header">
      <div class="page-title">业务专题</div>
      <div class="page-subtitle">聚焦重点领域，深度跟踪</div>
    </div>

    <div v-if="loading" class="loading-state">
      <van-loading type="spinner" color="#1a2942" />
      <span>加载中...</span>
    </div>

    <div v-else class="topics-list">
      <div
        v-for="topic in topics"
        :key="topic.id"
        class="topic-card"
        @click="goToTopicDetail(topic.id)"
      >
        <div class="topic-cover" v-if="topic.cover_image">
          <img :src="topic.cover_image" :alt="topic.title" />
        </div>
        <div class="topic-cover placeholder" v-else>
          <span class="cover-icon">📋</span>
        </div>

        <div class="topic-info">
          <div class="topic-title">{{ topic.title }}</div>
          <div class="topic-desc ellipsis-2" v-if="topic.description">
            {{ topic.description }}
          </div>

          <div class="topic-stats">
            <div class="stat-item">
              <span class="stat-num">{{ topic.total_count || 0 }}</span>
              <span class="stat-label">资讯</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ topic.month_new_count || 0 }}</span>
              <span class="stat-label">本月新增</span>
            </div>
            <div class="stat-item">
              <span class="stat-num high-value">{{ topic.high_value_count || 0 }}</span>
              <span class="stat-label">高价值</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="topics.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <div class="empty-text">暂无专题</div>
      </div>
    </div>

    <!-- 底部TabBar -->
    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TabBar from '@/components/TabBar.vue'
import { getTopics, type TopicInfo } from '@/api/news'

const router = useRouter()

const topics = ref<TopicInfo[]>([])
const loading = ref(true)

onMounted(() => {
  loadTopics()
})

async function loadTopics() {
  loading.value = true
  try {
    const res = await getTopics()
    if (res.code === 0) {
      topics.value = res.data || []
    }
  } catch (error) {
    console.error('加载专题列表失败:', error)
  } finally {
    loading.value = false
  }
}

function goToTopicDetail(id: string) {
  router.push(`/topics/${id}`)
}
</script>

<style lang="scss" scoped>
.topics-page {
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #1a2942 0%, #2c3e5a 100%);
  color: #fff;
  padding: 20px 16px 24px;
  padding-top: calc(20px + env(safe-area-inset-top));

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

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  gap: 12px;
  color: #8c8c8c;
  font-size: 14px;
}

.topics-list {
  padding: 16px 12px 20px;
}

.topic-card {
  background-color: #fff;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }
}

.topic-cover {
  width: 100%;
  height: 120px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &.placeholder {
    .cover-icon {
      font-size: 48px;
      opacity: 0.5;
    }
  }
}

.topic-info {
  padding: 16px;
}

.topic-title {
  font-size: 17px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 8px;
}

.topic-desc {
  font-size: 13px;
  color: #8c8c8c;
  line-height: 1.6;
  margin-bottom: 16px;
}

.topic-stats {
  display: flex;
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;

  .stat-num {
    font-size: 18px;
    font-weight: 700;
    color: #1a2942;
    margin-bottom: 2px;

    &.high-value {
      color: #f39c12;
    }
  }

  .stat-label {
    font-size: 11px;
    color: #8c8c8c;
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

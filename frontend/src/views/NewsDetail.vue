<template>
  <div class="news-detail-page">
    <!-- 顶部导航 -->
    <div class="nav-bar">
      <div class="nav-back" @click="goBack">
        <span>←</span>
      </div>
      <div class="nav-title">资讯详情</div>
      <div class="nav-actions">
        <span @click="shareNews">分享</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <van-loading type="spinner" color="#1a56db" />
      <span>加载中...</span>
    </div>

    <div v-else-if="news" class="detail-content">
      <!-- 标题 -->
      <h1 class="news-title">{{ news.title }}</h1>

      <!-- 元信息 -->
      <div class="news-meta">
        <span class="source">{{ news.source_channel }}</span>
        <span class="date">{{ formatDate(news.publish_date, 'YYYY-MM-DD HH:mm') }}</span>
        <span class="views">👁 {{ news.view_count || 0 }}</span>
      </div>

      <!-- 标签 -->
      <div class="news-tags" v-if="hasTags">
        <span
          v-if="news.info_type"
          class="tag"
          :style="{ backgroundColor: infoTypeColor + '20', color: infoTypeColor }"
        >
          {{ infoTypeName }}
        </span>
        <span
          v-if="news.business_category"
          class="tag"
          :style="{ backgroundColor: businessColor + '20', color: businessColor }"
        >
          {{ businessName }}
        </span>
        <span v-for="area in news.area_tags" :key="area" class="tag tag-area">
          {{ areaName(area) }}
        </span>
        <span v-for="industry in news.industry_tags" :key="industry" class="tag tag-industry">
          {{ industryName(industry) }}
        </span>
      </div>

      <!-- 质量分 -->
      <div class="quality-badge">
        <span class="quality-label">商机价值</span>
        <span class="quality-score" :style="{ color: qualityColor }">{{ news.quality_score }}</span>
        <span class="quality-unit">分</span>
      </div>

      <!-- 摘要 -->
      <div class="summary-section" v-if="news.content_summary">
        <div class="section-title">📝 核心摘要</div>
        <div class="summary-content">{{ news.content_summary }}</div>
      </div>

      <!-- 业务启示 -->
      <div class="tip-section" v-if="news.business_tip">
        <div class="section-title">💡 业务启示</div>
        <div class="tip-content">{{ news.business_tip }}</div>
      </div>

      <!-- 正文 -->
      <div class="content-section" v-if="news.content_raw">
        <div class="section-title">📄 详细内容</div>
        <div class="content-text">{{ news.content_raw }}</div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <a
          v-if="news.source_url"
          class="action-btn source-link"
          :href="news.source_url"
          target="_blank"
          rel="noopener noreferrer"
        >
          🔗 查看原文
        </a>
        <button class="action-btn secondary" @click="collectNews">
          ⭐ 收藏
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getNewsDetail, type NewsItem } from '@/api/news'
import {
  formatDate,
  businessCategoryMap,
  infoTypeMap,
  areaTagMap,
  industryTagMap,
  getQualityScoreColor,
} from '@/utils/format'

const route = useRoute()
const router = useRouter()

const news = ref<NewsItem | null>(null)
const loading = ref(true)

const hasTags = computed(() => {
  if (!news.value) return false
  return (
    news.value.info_type ||
    news.value.business_category ||
    (news.value.area_tags && news.value.area_tags.length > 0) ||
    (news.value.industry_tags && news.value.industry_tags.length > 0)
  )
})

const infoTypeName = computed(() => {
  return infoTypeMap[news.value?.info_type || '']?.name || news.value?.info_type
})

const infoTypeColor = computed(() => {
  return infoTypeMap[news.value?.info_type || '']?.color || '#999'
})

const businessName = computed(() => {
  return businessCategoryMap[news.value?.business_category || '']?.name || news.value?.business_category
})

const businessColor = computed(() => {
  return businessCategoryMap[news.value?.business_category || '']?.color || '#999'
})

const qualityColor = computed(() => {
  return getQualityScoreColor(news.value?.quality_score || 0)
})

function areaName(code: string): string {
  return areaTagMap[code] || code
}

function industryName(code: string): string {
  return industryTagMap[code] || code
}

onMounted(() => {
  loadDetail()
})

async function loadDetail() {
  const id = route.params.id as string
  if (!id) return

  loading.value = true
  try {
    const res = await getNewsDetail(id)
    if (res.code === 0) {
      news.value = res.data
    }
  } catch (error) {
    console.error('加载资讯详情失败:', error)
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.back()
}

function shareNews() {
  showToast('分享功能开发中')
}

function collectNews() {
  showToast('收藏成功')
}
</script>

<style lang="scss" scoped>
.news-detail-page {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 80px;
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
  background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
  border-bottom: none;

  .nav-back {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    cursor: pointer;
    color: #fff;
  }

  .nav-title {
    font-size: 16px;
    font-weight: 600;
    color: #fff;
  }

  .nav-actions {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
    cursor: pointer;
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

.detail-content {
  padding: 16px;
}

.news-title {
  font-size: 20px;
  font-weight: 700;
  color: #262626;
  line-height: 1.5;
  margin-bottom: 12px;
}

.news-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.news-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;

  .tag {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 12px;
    background-color: #f5f5f5;
    color: #595959;
  }

  .tag-area {
    background-color: #e6f7ff;
    color: #1890ff;
  }

  .tag-industry {
    background-color: #f6ffed;
    color: #52c41a;
  }
}

.quality-badge {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #fff7e6 0%, #fffbe6 100%);
  border-radius: 8px;
  margin-bottom: 12px;

  .quality-label {
    font-size: 12px;
    color: #8c8c8c;
  }

  .quality-score {
    font-size: 28px;
    font-weight: 700;
  }

  .quality-unit {
    font-size: 12px;
    color: #8c8c8c;
  }
}

.summary-section,
.tip-section,
.content-section {
  background-color: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 12px;
}

.summary-content {
  font-size: 14px;
  color: #595959;
  line-height: 1.8;
}

.tip-section {
  background: linear-gradient(135deg, #fff7e6 0%, #fffbe6 100%);
  border: 1px solid #ffe58f;

  .section-title {
    color: #ad6800;
  }

  .tip-content {
    font-size: 14px;
    color: #ad6800;
    line-height: 1.8;
  }
}

.content-text {
  font-size: 14px;
  color: #262626;
  line-height: 1.8;
  white-space: pre-wrap;
}

.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background-color: #fff;
  border-top: 1px solid #f0f0f0;
}

.action-btn {
  flex: 1;
  height: 44px;
  border-radius: 22px;
  font-size: 15px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s;

  &.primary {
    background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
    color: #fff;
  }

  &.secondary {
    background-color: #f5f5f5;
    color: #595959;
  }

  &.source-link {
    background-color: #eff6ff;
    color: #1a56db;
    text-decoration: none;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &:active {
    transform: scale(0.98);
  }
}
</style>

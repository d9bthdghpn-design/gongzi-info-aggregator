<template>
  <div class="news-card" @click="handleClick">
    <!-- 标题 -->
    <div class="news-title ellipsis-2">{{ news.title }}</div>

    <!-- 标签行 -->
    <div class="news-tags" v-if="hasTags">
      <span
        v-if="news.business_category"
        class="tag tag-action"
        :style="{ backgroundColor: businessColor + '18', color: businessColor, borderColor: businessColor + '40' }"
      >
        {{ businessName }}
      </span>
      <span
        v-for="area in news.area_tags?.slice(0, 2)"
        :key="area"
        class="tag tag-area"
      >
        {{ areaName(area) }}
      </span>
      <span
        v-for="ind in news.industry_tags?.slice(0, 1)"
        :key="ind"
        class="tag tag-industry"
      >
        {{ industryName(ind) }}
      </span>
    </div>

    <!-- 摘要 -->
    <div class="news-summary ellipsis-2" v-if="news.content_summary">
      {{ news.content_summary }}
    </div>

    <!-- 业务启示 -->
    <div class="news-tip" v-if="news.business_tip">
      <span class="tip-icon">💡</span>
      <span class="tip-text ellipsis-2">{{ news.business_tip }}</span>
    </div>

    <!-- 底部信息 -->
    <div class="news-footer">
      <div class="footer-meta">
        <span class="source">{{ news.source_channel }}</span>
        <span class="date">{{ formatRelativeTime(news.publish_date) }}</span>
        <span class="quality-score" :style="{ color: qualityColor }">
          {{ news.quality_score }}分
        </span>
      </div>
      <!-- 两按钮：原文 + 详情 -->
      <div class="action-buttons">
        <a
          v-if="news.source_url"
          class="action-btn btn-source"
          :href="news.source_url"
          target="_blank"
          rel="noopener noreferrer"
          @click.stop
        >
          🔗 原文
        </a>
        <button class="action-btn btn-detail" @click.stop="handleClick">
          📄 详情
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { NewsItem } from '@/api/news'
import {
  formatRelativeTime,
  businessCategoryMap,
  areaTagMap,
  industryTagMap,
  getQualityScoreColor,
} from '@/utils/format'

const props = defineProps<{
  news: NewsItem
}>()

const emit = defineEmits<{
  (e: 'click', news: NewsItem): void
}>()

const router = useRouter()

const hasTags = computed(() => {
  return (
    props.news.business_category ||
    (props.news.area_tags && props.news.area_tags.length > 0) ||
    (props.news.industry_tags && props.news.industry_tags.length > 0)
  )
})

const businessName = computed(() => {
  return businessCategoryMap[props.news.business_category || '']?.name || props.news.business_category
})

const businessColor = computed(() => {
  return businessCategoryMap[props.news.business_category || '']?.color || '#999'
})

const qualityColor = computed(() => {
  return getQualityScoreColor(props.news.quality_score || 0)
})

function areaName(code: string): string {
  return areaTagMap[code] || code
}

function industryName(code: string): string {
  return industryTagMap[code] || code
}

function handleClick() {
  emit('click', props.news)
  router.push(`/news/${props.news.id}`)
}
</script>

<style lang="scss" scoped>
.news-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;

  &:active {
    transform: scale(0.98);
  }
}

.news-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.5;
  margin-bottom: 8px;
}

.news-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 8px;

  .tag {
    display: inline-flex;
    align-items: center;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 10px;
    line-height: 1.5;
    border: 1px solid transparent;
  }

  .tag-action {
    font-weight: 600;
  }

  .tag-area {
    background: #f0f2f5;
    color: #595959;
  }

  .tag-industry {
    background: #f0f9ff;
    color: #0369a1;
  }
}

.news-summary {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 8px;
}

.news-tip {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  padding: 8px 10px;
  background: linear-gradient(135deg, #fff7e6 0%, #fffbe6 100%);
  border-radius: 8px;
  margin-bottom: 10px;

  .tip-icon {
    font-size: 12px;
    flex-shrink: 0;
  }

  .tip-text {
    font-size: 11px;
    color: #ad6800;
    line-height: 1.5;
    flex: 1;
  }
}

.news-footer {
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;

  .footer-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;

    .source {
      font-size: 11px;
      color: #9ca3af;
    }

    .date {
      font-size: 11px;
      color: #d1d5db;
    }

    .quality-score {
      font-size: 11px;
      font-weight: 700;
      margin-left: auto;
    }
  }
}

.action-buttons {
  display: flex;
  gap: 6px;

  .action-btn {
    flex: 1;
    padding: 6px 4px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
    border: 1px solid;
    text-align: center;
    text-decoration: none;
    transition: all 0.15s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 2px;

    &:active {
      transform: scale(0.95);
    }
  }

  .btn-source {
    background: #fff;
    color: #1a56db;
    border-color: #1a56db;
  }

  .btn-detail {
    background: #f3f4f6;
    color: #4b5563;
    border-color: #e5e7eb;
  }
}
</style>

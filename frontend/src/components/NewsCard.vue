<template>
  <div class="news-card" @click="handleClick">
    <!-- 标题 -->
    <div class="news-title ellipsis-2">{{ news.title }}</div>

    <!-- 标签行 -->
    <div class="news-tags" v-if="hasTags">
      <span
        v-if="news.info_type"
        class="tag tag-info-type"
        :style="{ backgroundColor: infoTypeColor + '20', color: infoTypeColor }"
      >
        {{ infoTypeName }}
      </span>
      <span
        v-if="news.business_category"
        class="tag tag-business"
        :style="{ backgroundColor: businessColor + '20', color: businessColor }"
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
      <div class="footer-left">
        <span class="source">{{ news.source_channel }}</span>
        <span class="date">{{ formatRelativeTime(news.publish_date) }}</span>
        <a
          v-if="news.source_url"
          class="source-link"
          :href="news.source_url"
          target="_blank"
          rel="noopener noreferrer"
          @click.stop
        >
          🔗 原文
        </a>
      </div>
      <div class="footer-right">
        <span class="quality-score" :style="{ color: qualityColor }">
          {{ news.quality_score }}分
        </span>
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
  infoTypeMap,
  areaTagMap,
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
    props.news.info_type ||
    props.news.business_category ||
    (props.news.area_tags && props.news.area_tags.length > 0)
  )
})

const infoTypeName = computed(() => {
  return infoTypeMap[props.news.info_type || '']?.name || props.news.info_type
})

const infoTypeColor = computed(() => {
  return infoTypeMap[props.news.info_type || '']?.color || '#999'
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

function handleClick() {
  emit('click', props.news)
  router.push(`/news/${props.news.id}`)
}
</script>

<style lang="scss" scoped>
.news-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;

  &:active {
    transform: scale(0.98);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  }
}

.news-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  line-height: 1.5;
  margin-bottom: 10px;
}

.news-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;

  .tag {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    line-height: 1.5;
  }
}

.news-summary {
  font-size: 13px;
  color: #595959;
  line-height: 1.6;
  margin-bottom: 10px;
}

.news-tip {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #fff7e6 0%, #fffbe6 100%);
  border-radius: 8px;
  margin-bottom: 12px;

  .tip-icon {
    font-size: 14px;
    flex-shrink: 0;
  }

  .tip-text {
    font-size: 12px;
    color: #ad6800;
    line-height: 1.6;
    flex: 1;
  }
}

.news-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;

  .footer-left {
    display: flex;
    align-items: center;
    gap: 12px;

    .source {
      font-size: 12px;
      color: #8c8c8c;
    }

    .date {
      font-size: 12px;
      color: #bfbfbf;
    }

    .source-link {
      font-size: 12px;
      color: #1890ff;
      text-decoration: none;
      margin-left: 4px;
    }
  }

  .footer-right {
    .quality-score {
      font-size: 12px;
      font-weight: 600;
    }
  }
}
</style>

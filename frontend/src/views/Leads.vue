<template>
  <div class="leads-page page-container">
    <!-- 顶部Header -->
    <div class="page-header">
      <div class="header-top">
        <div>
          <div class="page-title">线索管理</div>
          <div class="page-subtitle">商机跟踪，高效转化</div>
        </div>
        <div class="header-btn" @click="goToCreate">
          <span>+</span> 上报
        </div>
      </div>
    </div>

    <!-- Tab切换 -->
    <div class="tab-switch">
      <div
        class="tab-item"
        :class="{ active: activeTab === 'mine' }"
        @click="switchTab('mine')"
      >
        我的线索
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'public' }"
        @click="switchTab('public')"
      >
        公海池
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <div class="filter-item" @click="showStatusFilter = true">
        <span>{{ currentStatusLabel }}</span>
        <span class="filter-arrow">▼</span>
      </div>
      <div class="filter-item" @click="showPriorityFilter = true">
        <span>{{ currentPriorityLabel }}</span>
        <span class="filter-arrow">▼</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <van-loading type="spinner" color="#1a56db" />
      <span>加载中...</span>
    </div>

    <div v-else class="leads-list">
      <div
        v-for="lead in leads"
        :key="lead.id"
        class="lead-card"
        @click="goToDetail(lead.id)"
      >
        <div class="lead-header">
          <div class="company-name ellipsis">{{ lead.company_name }}</div>
          <div
            class="status-tag"
            :style="{ backgroundColor: statusColor(lead.status) + '20', color: statusColor(lead.status) }"
          >
            {{ statusName(lead.status) }}
          </div>
        </div>

        <div class="lead-info">
          <div class="info-row" v-if="lead.contact_person">
            <span class="info-label">联系人</span>
            <span class="info-value">{{ lead.contact_person }} {{ lead.contact_title || '' }}</span>
          </div>
          <div class="info-row" v-if="lead.industry || lead.area">
            <span class="info-label">行业/区域</span>
            <span class="info-value">
              {{ industryName(lead.industry) || '-' }} / {{ areaName(lead.area) || '-' }}
            </span>
          </div>
          <div class="info-row" v-if="lead.project_desc">
            <span class="info-label">项目描述</span>
            <span class="info-value ellipsis-2">{{ lead.project_desc }}</span>
          </div>
        </div>

        <div class="lead-footer">
          <div class="footer-left">
            <span
              class="priority-dot"
              :style="{ backgroundColor: priorityColor(lead.priority) }"
            ></span>
            <span class="priority-text">{{ priorityName(lead.priority) }}优先级</span>
          </div>
          <div class="footer-right">
            <span class="update-time">{{ formatRelativeTime(lead.updated_at) }}</span>
          </div>
        </div>

        <!-- 公海池显示领取按钮 -->
        <div v-if="activeTab === 'public'" class="lead-action" @click.stop="claimLead(lead.id)">
          <button class="claim-btn">领取</button>
        </div>
      </div>

      <div v-if="leads.length === 0" class="empty-state">
        <div class="empty-icon">🎯</div>
        <div class="empty-text">暂无线索</div>
        <button class="create-btn" @click="goToCreate">上报线索</button>
      </div>

      <div v-if="hasMore" class="load-more" @click="loadMore">
        <span v-if="!loadingMore">加载更多</span>
        <van-loading v-else type="spinner" size="20px" color="#1a56db" />
      </div>
    </div>

    <!-- 底部TabBar -->
    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import TabBar from '@/components/TabBar.vue'
import {
  getMyLeads,
  getPublicPoolLeads,
  claimLead as claimLeadApi,
  type LeadItem,
} from '@/api/leads'
import {
  formatRelativeTime,
  leadStatusMap,
  priorityMap,
  industryTagMap,
  areaTagMap,
} from '@/utils/format'

const router = useRouter()

const activeTab = ref<'mine' | 'public'>('mine')
const leads = ref<LeadItem[]>([])
const loading = ref(true)
const loadingMore = ref(false)
const page = ref(1)
const pageSize = 20
const hasMore = ref(true)

const statusFilter = ref('')
const priorityFilter = ref('')
const showStatusFilter = ref(false)
const showPriorityFilter = ref(false)

const currentStatusLabel = computed(() => {
  if (!statusFilter.value) return '全部状态'
  return leadStatusMap[statusFilter.value]?.name || statusFilter.value
})

const currentPriorityLabel = computed(() => {
  if (!priorityFilter.value) return '全部优先级'
  return priorityMap[Number(priorityFilter.value)]?.name || priorityFilter.value
})

onMounted(() => {
  loadLeads()
})

async function loadLeads() {
  loading.value = true
  page.value = 1
  hasMore.value = true

  try {
    let res
    if (activeTab.value === 'mine') {
      res = await getMyLeads(page.value, pageSize)
    } else {
      res = await getPublicPoolLeads(page.value, pageSize)
    }

    if (res.code === 0) {
      leads.value = res.data || []
      hasMore.value = (res.total || 0) > pageSize
    }
  } catch (error) {
    console.error('加载线索列表失败:', error)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return

  loadingMore.value = true
  page.value++

  try {
    let res
    if (activeTab.value === 'mine') {
      res = await getMyLeads(page.value, pageSize)
    } else {
      res = await getPublicPoolLeads(page.value, pageSize)
    }

    if (res.code === 0) {
      leads.value = [...leads.value, ...(res.data || [])]
      hasMore.value = leads.value.length < (res.total || 0)
    }
  } catch (error) {
    console.error('加载更多失败:', error)
  } finally {
    loadingMore.value = false
  }
}

function switchTab(tab: 'mine' | 'public') {
  activeTab.value = tab
  loadLeads()
}

function goToDetail(id: string) {
  router.push(`/leads/${id}`)
}

function goToCreate() {
  router.push('/leads/create')
}

async function claimLead(id: string) {
  try {
    await showConfirmDialog({
      title: '确认领取',
      message: '领取后该线索将进入您的个人线索池',
    })

    const res = await claimLeadApi(id)
    if (res.code === 0) {
      showToast('领取成功')
      loadLeads()
    }
  } catch (error) {
    // 用户取消
  }
}

function statusName(status: string): string {
  return leadStatusMap[status]?.name || status
}

function statusColor(status: string): string {
  return leadStatusMap[status]?.color || '#999'
}

function priorityName(priority: number): string {
  return priorityMap[priority]?.name || '中'
}

function priorityColor(priority: number): string {
  return priorityMap[priority]?.color || '#faad14'
}

function industryName(code?: string): string {
  if (!code) return ''
  return industryTagMap[code] || code
}

function areaName(code?: string): string {
  if (!code) return ''
  return areaTagMap[code] || code
}
</script>

<style lang="scss" scoped>
.leads-page {
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
  color: #fff;
  padding: 20px 16px 20px;
  padding-top: calc(20px + env(safe-area-inset-top));

  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .page-title {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .page-subtitle {
    font-size: 13px;
    opacity: 0.7;
  }

  .header-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 8px 16px;
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 20px;
    font-size: 14px;
    cursor: pointer;
  }
}

.tab-switch {
  display: flex;
  background-color: #fff;
  margin: 0 12px;
  margin-top: -10px;
  border-radius: 12px;
  padding: 4px;
  position: relative;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 10px 0;
  font-size: 14px;
  color: #8c8c8c;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;

  &.active {
    background-color: #1a56db;
    color: #fff;
    font-weight: 500;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background-color: #fff;
  border-radius: 16px;
  font-size: 12px;
  color: #595959;
  cursor: pointer;

  .filter-arrow {
    font-size: 8px;
    color: #bfbfbf;
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

.leads-list {
  padding: 0 12px 20px;
}

.lead-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;

  &:active {
    background-color: #fafafa;
  }
}

.lead-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .company-name {
    font-size: 16px;
    font-weight: 600;
    color: #262626;
    flex: 1;
    margin-right: 12px;
  }

  .status-tag {
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    flex-shrink: 0;
  }
}

.lead-info {
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
  font-size: 13px;

  &:last-child {
    margin-bottom: 0;
  }

  .info-label {
    color: #8c8c8c;
    width: 70px;
    flex-shrink: 0;
  }

  .info-value {
    color: #595959;
    flex: 1;
    line-height: 1.5;
  }
}

.lead-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;

  .footer-left {
    display: flex;
    align-items: center;
    gap: 6px;

    .priority-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .priority-text {
      font-size: 12px;
      color: #8c8c8c;
    }
  }

  .footer-right {
    .update-time {
      font-size: 12px;
      color: #bfbfbf;
    }
  }
}

.lead-action {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  text-align: right;

  .claim-btn {
    padding: 6px 20px;
    background-color: #1a56db;
    color: #fff;
    border: none;
    border-radius: 16px;
    font-size: 13px;
    cursor: pointer;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;

  .empty-icon {
    font-size: 64px;
    margin-bottom: 16px;
  }

  .empty-text {
    font-size: 14px;
    color: #8c8c8c;
    margin-bottom: 20px;
  }

  .create-btn {
    padding: 10px 24px;
    background-color: #1a56db;
    color: #fff;
    border: none;
    border-radius: 20px;
    font-size: 14px;
    cursor: pointer;
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

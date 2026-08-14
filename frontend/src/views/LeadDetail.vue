<template>
  <div class="lead-detail-page">
    <!-- 顶部导航 -->
    <div class="nav-bar">
      <div class="nav-back" @click="goBack">
        <span>←</span>
      </div>
      <div class="nav-title">线索详情</div>
      <div class="nav-actions">
        <span @click="showMore = true">⋯</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <van-loading type="spinner" color="#1a56db" />
      <span>加载中...</span>
    </div>

    <div v-else-if="lead" class="detail-content">
      <!-- 企业信息卡片 -->
      <div class="info-card">
        <div class="card-header">
          <div class="company-name">{{ lead.company_name }}</div>
          <div
            class="status-tag"
            :style="{ backgroundColor: statusColor + '20', color: statusColor }"
          >
            {{ statusName }}
          </div>
        </div>

        <div class="info-list">
          <div class="info-row" v-if="lead.credit_code">
            <span class="info-label">统一社会信用代码</span>
            <span class="info-value">{{ lead.credit_code }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">所属行业</span>
            <span class="info-value">{{ industryName }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">所在区域</span>
            <span class="info-value">{{ areaName }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">优先级</span>
            <span class="info-value" :style="{ color: priorityColor }">
              ● {{ priorityName }}
            </span>
          </div>
        </div>
      </div>

      <!-- 联系人卡片 -->
      <div class="info-card" v-if="lead.contact_person || lead.contact_phone">
        <div class="card-title">联系人</div>
        <div class="info-list">
          <div class="info-row" v-if="lead.contact_person">
            <span class="info-label">姓名</span>
            <span class="info-value">{{ lead.contact_person }} {{ lead.contact_title || '' }}</span>
          </div>
          <div class="info-row" v-if="lead.contact_phone">
            <span class="info-label">电话</span>
            <span class="info-value link">{{ lead.contact_phone }}</span>
          </div>
        </div>
      </div>

      <!-- 商机信息卡片 -->
      <div class="info-card">
        <div class="card-title">商机信息</div>
        <div class="info-list">
          <div class="info-row" v-if="lead.intent_business && lead.intent_business.length > 0">
            <span class="info-label">意向业务</span>
            <div class="info-value tags">
              <span
                v-for="biz in lead.intent_business"
                :key="biz"
                class="biz-tag"
                :style="{ backgroundColor: businessColor(biz) + '20', color: businessColor(biz) }"
              >
                {{ businessName(biz) }}
              </span>
            </div>
          </div>
          <div class="info-row" v-if="lead.project_desc">
            <span class="info-label">项目描述</span>
            <span class="info-value desc">{{ lead.project_desc }}</span>
          </div>
          <div class="info-row" v-if="lead.expected_date">
            <span class="info-label">预计时间</span>
            <span class="info-value">{{ formatDate(lead.expected_date) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">线索来源</span>
            <span class="info-value">{{ lead.lead_source }}</span>
          </div>
        </div>
      </div>

      <!-- 跟进记录 -->
      <div class="info-card">
        <div class="card-title">
          <span>跟进记录</span>
          <span class="add-btn" @click="showFollowupForm = true">+ 添加</span>
        </div>

        <div v-if="followups.length === 0" class="empty-followup">
          暂无跟进记录
        </div>

        <div v-else class="followup-list">
          <div v-for="item in followups" :key="item.id" class="followup-item">
            <div class="followup-dot"></div>
            <div class="followup-content">
              <div class="followup-header">
                <span class="followup-type">{{ followupTypeName(item.followup_type) }}</span>
                <span class="followup-time">{{ formatDateTime(item.followup_time) }}</span>
              </div>
              <div class="followup-text">{{ item.content }}</div>
              <div class="followup-next" v-if="item.next_action">
                下一步：{{ item.next_action }}
                <span v-if="item.next_time">（{{ formatDate(item.next_time) }}）</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="action-bar" v-if="lead">
      <button class="action-btn secondary" @click="handleRelease">
        释放
      </button>
      <button class="action-btn primary" @click="showFollowupForm = true">
        添加跟进
      </button>
    </div>

    <!-- 跟进弹窗 -->
    <van-popup
      v-model:show="showFollowupForm"
      position="bottom"
      round
      :style="{ height: '60%' }"
    >
      <div class="followup-form">
        <div class="form-header">
          <span>添加跟进记录</span>
          <span class="close-btn" @click="showFollowupForm = false">✕</span>
        </div>

        <div class="form-body">
          <div class="form-item">
            <label>跟进方式</label>
            <select v-model="followupForm.followup_type">
              <option value="phone">电话</option>
              <option value="visit">拜访</option>
              <option value="email">邮件</option>
              <option value="meeting">会议</option>
              <option value="other">其他</option>
            </select>
          </div>

          <div class="form-item">
            <label>跟进内容 <span class="required">*</span></label>
            <textarea
              v-model="followupForm.content"
              placeholder="请输入跟进内容"
              rows="4"
            ></textarea>
          </div>

          <div class="form-item">
            <label>下一步计划</label>
            <input
              v-model="followupForm.next_action"
              type="text"
              placeholder="请输入下一步计划"
            />
          </div>

          <div class="form-item">
            <label>下次跟进时间</label>
            <input
              v-model="followupForm.next_time"
              type="date"
              placeholder="选择日期"
            />
          </div>
        </div>

        <div class="form-footer">
          <button
            class="submit-btn"
            :class="{ disabled: submittingFollowup }"
            :disabled="submittingFollowup"
            @click="submitFollowup"
          >
            <van-loading v-if="submittingFollowup" type="spinner" size="18px" color="#fff" />
            <span v-else>提交</span>
          </button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import {
  getLeadDetail,
  getLeadFollowups,
  addLeadFollowup,
  releaseLead,
  type LeadItem,
  type LeadFollowup,
} from '@/api/leads'
import {
  formatDate,
  formatDateTime,
  leadStatusMap,
  priorityMap,
  industryTagMap,
  areaTagMap,
  businessCategoryMap,
} from '@/utils/format'

const route = useRoute()
const router = useRouter()

const lead = ref<LeadItem | null>(null)
const followups = ref<LeadFollowup[]>([])
const loading = ref(true)
const showMore = ref(false)
const showFollowupForm = ref(false)
const submittingFollowup = ref(false)

const followupForm = ref({
  followup_type: 'phone',
  content: '',
  next_action: '',
  next_time: '',
})

const statusName = computed(() => leadStatusMap[lead.value?.status || '']?.name || '-')
const statusColor = computed(() => leadStatusMap[lead.value?.status || '']?.color || '#999')
const priorityName = computed(() => priorityMap[lead.value?.priority || 2]?.name || '中')
const priorityColor = computed(() => priorityMap[lead.value?.priority || 2]?.color || '#faad14')
const industryName = computed(() => industryTagMap[lead.value?.industry || ''] || '-')
const areaName = computed(() => areaTagMap[lead.value?.area || ''] || '-')

const followupTypeMap: Record<string, string> = {
  phone: '电话沟通',
  visit: '上门拜访',
  email: '邮件往来',
  meeting: '会议交流',
  other: '其他',
}

function followupTypeName(type: string): string {
  return followupTypeMap[type] || type
}

function businessName(code: string): string {
  return businessCategoryMap[code]?.name || code
}

function businessColor(code: string): string {
  return businessCategoryMap[code]?.color || '#999'
}

onMounted(() => {
  loadDetail()
})

async function loadDetail() {
  const id = route.params.id as string
  if (!id) return

  loading.value = true
  try {
    const [detailRes, followupsRes] = await Promise.all([
      getLeadDetail(id),
      getLeadFollowups(id, 1, 50),
    ])

    if (detailRes.code === 0) {
      lead.value = detailRes.data
    }
    if (followupsRes.code === 0) {
      followups.value = followupsRes.data || []
    }
  } catch (error) {
    console.error('加载线索详情失败:', error)
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.back()
}

async function handleRelease() {
  try {
    await showConfirmDialog({
      title: '确认释放',
      message: '释放后线索将进入公海池，确定要释放吗？',
    })

    const res = await releaseLead(route.params.id as string)
    if (res.code === 0) {
      showToast('释放成功')
      router.back()
    }
  } catch (error) {
    // 用户取消
  }
}

async function submitFollowup() {
  if (!followupForm.value.content) {
    showToast('请输入跟进内容')
    return
  }

  submittingFollowup.value = true
  try {
    const res = await addLeadFollowup(route.params.id as string, followupForm.value)
    if (res.code === 0) {
      showToast('提交成功')
      showFollowupForm.value = false
      followupForm.value = {
        followup_type: 'phone',
        content: '',
        next_action: '',
        next_time: '',
      }
      loadDetail()
    }
  } catch (error) {
    showToast('提交失败')
  } finally {
    submittingFollowup.value = false
  }
}
</script>

<style lang="scss" scoped>
.lead-detail-page {
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
  background-color: #fff;
  border-bottom: 1px solid #f0f0f0;

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
    color: #262626;
  }

  .nav-actions {
    font-size: 18px;
    color: #8c8c8c;
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
  padding: 12px;
}

.info-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;

  .company-name {
    font-size: 18px;
    font-weight: 600;
    color: #262626;
    flex: 1;
    margin-right: 12px;
  }

  .status-tag {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    flex-shrink: 0;
  }
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .add-btn {
    font-size: 13px;
    color: #1a56db;
    font-weight: normal;
    cursor: pointer;
  }
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  font-size: 14px;

  .info-label {
    color: #8c8c8c;
    width: 100px;
    flex-shrink: 0;
  }

  .info-value {
    color: #262626;
    flex: 1;
    line-height: 1.5;

    &.link {
      color: #1890ff;
    }

    &.desc {
      line-height: 1.6;
    }

    &.tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
  }
}

.biz-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.empty-followup {
  text-align: center;
  padding: 20px 0;
  color: #bfbfbf;
  font-size: 13px;
}

.followup-list {
  position: relative;
  padding-left: 20px;
}

.followup-item {
  position: relative;
  padding-bottom: 20px;

  &:last-child {
    padding-bottom: 0;
  }
}

.followup-dot {
  position: absolute;
  left: -20px;
  top: 4px;
  width: 10px;
  height: 10px;
  background-color: #1a56db;
  border-radius: 50%;

  &::before {
    content: '';
    position: absolute;
    top: 10px;
    left: 4px;
    width: 2px;
    height: calc(100% + 10px);
    background-color: #e8e8e8;
  }
}

.followup-item:last-child .followup-dot::before {
  display: none;
}

.followup-content {
  .followup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;

    .followup-type {
      font-size: 13px;
      font-weight: 500;
      color: #262626;
    }

    .followup-time {
      font-size: 12px;
      color: #bfbfbf;
    }
  }

  .followup-text {
    font-size: 13px;
    color: #595959;
    line-height: 1.6;
    margin-bottom: 6px;
  }

  .followup-next {
    font-size: 12px;
    color: #1890ff;
  }
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

  &.primary {
    background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
    color: #fff;
  }

  &.secondary {
    background-color: #f5f5f5;
    color: #595959;
  }
}

.followup-form {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 16px;
  font-weight: 600;

  .close-btn {
    font-size: 18px;
    color: #bfbfbf;
    cursor: pointer;
  }
}

.form-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.form-item {
  margin-bottom: 16px;

  label {
    display: block;
    font-size: 13px;
    color: #595959;
    margin-bottom: 8px;

    .required {
      color: #f5222d;
    }
  }

  input,
  select,
  textarea {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    font-size: 14px;
    color: #262626;
    background-color: #fafafa;
    outline: none;

    &:focus {
      border-color: #1a56db;
      background-color: #fff;
    }
  }

  textarea {
    resize: vertical;
    min-height: 80px;
  }
}

.form-footer {
  padding: 12px 16px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  border-top: 1px solid #f0f0f0;
}

.submit-btn {
  width: 100%;
  height: 44px;
  background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
  color: #fff;
  border: none;
  border-radius: 22px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;

  &.disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}
</style>

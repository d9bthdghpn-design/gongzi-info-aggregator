<template>
  <div class="lead-create-page">
    <!-- 顶部导航 -->
    <div class="nav-bar">
      <div class="nav-back" @click="goBack">
        <span>←</span>
      </div>
      <div class="nav-title">线索上报</div>
      <div class="nav-actions">
        <span @click="handleSubmit" :class="{ disabled: submitting }">提交</span>
      </div>
    </div>

    <div class="form-container">
      <!-- 企业信息 -->
      <div class="form-section">
        <div class="section-title">企业信息</div>

        <div class="form-item">
          <label>企业名称 <span class="required">*</span></label>
          <input
            v-model="form.company_name"
            type="text"
            placeholder="请输入企业名称"
          />
        </div>

        <div class="form-item">
          <label>统一社会信用代码</label>
          <input
            v-model="form.credit_code"
            type="text"
            placeholder="请输入统一社会信用代码"
          />
        </div>

        <div class="form-item row">
          <div class="form-item-half">
            <label>所属行业</label>
            <select v-model="form.industry">
              <option value="">请选择</option>
              <option v-for="(name, code) in industryOptions" :key="code" :value="code">
                {{ name }}
              </option>
            </select>
          </div>
          <div class="form-item-half">
            <label>所在区域</label>
            <select v-model="form.area">
              <option value="">请选择</option>
              <option v-for="(name, code) in areaOptions" :key="code" :value="code">
                {{ name }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- 联系人信息 -->
      <div class="form-section">
        <div class="section-title">联系人信息</div>

        <div class="form-item row">
          <div class="form-item-half">
            <label>联系人</label>
            <input
              v-model="form.contact_person"
              type="text"
              placeholder="姓名"
            />
          </div>
          <div class="form-item-half">
            <label>职务</label>
            <input
              v-model="form.contact_title"
              type="text"
              placeholder="职位"
            />
          </div>
        </div>

        <div class="form-item">
          <label>联系电话</label>
          <input
            v-model="form.contact_phone"
            type="tel"
            placeholder="请输入联系电话"
          />
        </div>
      </div>

      <!-- 商机信息 -->
      <div class="form-section">
        <div class="section-title">商机信息</div>

        <div class="form-item">
          <label>意向业务</label>
          <div class="checkbox-group">
            <label
              v-for="(item, code) in businessOptions"
              :key="code"
              class="checkbox-item"
              :class="{ checked: form.intent_business.includes(code) }"
              @click="toggleBusiness(code)"
            >
              <span class="checkbox-icon">{{ item.icon }}</span>
              <span>{{ item.name }}</span>
            </label>
          </div>
        </div>

        <div class="form-item">
          <label>项目描述</label>
          <textarea
            v-model="form.project_desc"
            placeholder="请描述项目背景、需求、预算等信息"
            rows="4"
          ></textarea>
        </div>

        <div class="form-item row">
          <div class="form-item-half">
            <label>优先级</label>
            <select v-model="form.priority">
              <option :value="3">高</option>
              <option :value="2">中</option>
              <option :value="1">低</option>
            </select>
          </div>
          <div class="form-item-half">
            <label>预计时间</label>
            <input
              v-model="form.expected_date"
              type="date"
              placeholder="预计落地时间"
            />
          </div>
        </div>

        <div class="form-item">
          <label>线索来源</label>
          <select v-model="form.lead_source">
            <option value="manual">手动录入</option>
            <option value="news">资讯转化</option>
            <option value="referral">客户转介绍</option>
            <option value="event">活动获取</option>
            <option value="other">其他</option>
          </select>
        </div>
      </div>

      <div class="submit-section">
        <button
          class="submit-btn"
          :class="{ disabled: submitting }"
          :disabled="submitting"
          @click="handleSubmit"
        >
          <van-loading v-if="submitting" type="spinner" size="20px" color="#fff" />
          <span v-else>提交线索</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { createLead } from '@/api/leads'
import { businessCategoryMap, industryTagMap, areaTagMap } from '@/utils/format'

const router = useRouter()
const route = useRoute()

const submitting = ref(false)

const form = reactive({
  company_name: '',
  credit_code: '',
  industry: '',
  area: '',
  contact_person: '',
  contact_title: '',
  contact_phone: '',
  intent_business: [] as string[],
  project_desc: '',
  priority: 2,
  expected_date: '',
  lead_source: 'manual',
  source_news_id: '',
})

const businessOptions = computed(() => {
  return Object.fromEntries(
    Object.entries(businessCategoryMap).map(([code, info]) => [code, { name: info.name, icon: info.icon }])
  )
})

const industryOptions = industryTagMap
const areaOptions = areaTagMap

onMounted(() => {
  const newsId = route.query.news_id as string
  if (newsId) {
    form.source_news_id = newsId
    form.lead_source = 'news'
  }
})

function toggleBusiness(code: string) {
  const index = form.intent_business.indexOf(code)
  if (index > -1) {
    form.intent_business.splice(index, 1)
  } else {
    form.intent_business.push(code)
  }
}

function goBack() {
  router.back()
}

async function handleSubmit() {
  if (!form.company_name) {
    showToast('请输入企业名称')
    return
  }

  submitting.value = true
  try {
    const res = await createLead(form)
    if (res.code === 0) {
      showToast('提交成功')
      setTimeout(() => {
        router.back()
      }, 1000)
    } else {
      showToast(res.message || '提交失败')
    }
  } catch (error) {
    showToast('提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
</script>

<script lang="ts">
import { computed } from 'vue'
</script>

<style lang="scss" scoped>
.lead-create-page {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 40px;
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
    font-size: 14px;
    color: #1a2942;
    cursor: pointer;
    font-weight: 500;

    &.disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.form-container {
  padding: 12px;
}

.form-section {
  background-color: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.form-item {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }

  &.row {
    display: flex;
    gap: 12px;
  }

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
    transition: border-color 0.2s;

    &:focus {
      border-color: #1a2942;
      background-color: #fff;
    }
  }

  textarea {
    resize: vertical;
    min-height: 80px;
  }

  &-half {
    flex: 1;
  }
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.checkbox-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid #e8e8e8;
  border-radius: 20px;
  font-size: 13px;
  color: #595959;
  cursor: pointer;
  transition: all 0.2s;

  .checkbox-icon {
    font-size: 14px;
  }

  &.checked {
    background-color: #e6f4ff;
    border-color: #1a2942;
    color: #1a2942;
  }
}

.submit-section {
  padding: 20px 0;
}

.submit-btn {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #1a2942 0%, #2c3e5a 100%);
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;

  &:active {
    transform: scale(0.98);
  }

  &.disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}
</style>

<template>
  <div class="dashboard-page">
    <!-- 顶部Header -->
    <div class="page-header">
      <h1 class="page-title">📊 商机转化看板</h1>
      <p class="page-subtitle">全链路商机转化追踪</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="dashboard-content">
      <!-- 核心指标卡 -->
      <div class="metric-cards">
        <div class="metric-card">
          <div class="metric-num">{{ data.total_opportunities }}</div>
          <div class="metric-label">系统商机</div>
        </div>
        <div class="metric-card">
          <div class="metric-num">{{ data.total_leads }}</div>
          <div class="metric-label">转线索</div>
        </div>
        <div class="metric-card highlight">
          <div class="metric-num">{{ data.conversion_rate }}%</div>
          <div class="metric-label">转化率</div>
        </div>
        <div class="metric-card">
          <div class="metric-num">{{ data.converted_leads }}</div>
          <div class="metric-label">已转化</div>
        </div>
      </div>

      <!-- 转化漏斗 -->
      <div class="panel">
        <div class="panel-title">🔻 转化漏斗</div>
        <div class="funnel">
          <div class="funnel-stage" style="width: 100%">
            <span class="funnel-label">商机数</span>
            <span class="funnel-value">{{ data.total_opportunities }}</span>
          </div>
          <div class="funnel-stage" :style="{ width: funnelPct(data.total_leads, data.total_opportunities) }">
            <span class="funnel-label">转线索</span>
            <span class="funnel-value">{{ data.total_leads }}</span>
          </div>
          <div class="funnel-stage" :style="{ width: funnelPct(data.active_leads, data.total_opportunities) }">
            <span class="funnel-label">跟进中</span>
            <span class="funnel-value">{{ data.active_leads }}</span>
          </div>
          <div class="funnel-stage" :style="{ width: funnelPct(data.converted_leads, data.total_opportunities) }">
            <span class="funnel-label">已转化</span>
            <span class="funnel-value">{{ data.converted_leads }}</span>
          </div>
        </div>
      </div>

      <!-- 金额统计 -->
      <div class="panel">
        <div class="panel-title">💰 金额统计（万元）</div>
        <div class="amount-row">
          <div class="amount-item">
            <div class="amount-num est">{{ formatAmount(data.total_estimated_amount) }}</div>
            <div class="amount-label">预估总金额</div>
          </div>
          <div class="amount-item">
            <div class="amount-num conv">{{ formatAmount(data.total_converted_amount) }}</div>
            <div class="amount-label">实际转化金额</div>
          </div>
        </div>
      </div>

      <!-- 行动分类分布 -->
      <div class="panel" v-if="data.category_breakdown.length > 0">
        <div class="panel-title">📂 行动分类分布</div>
        <div class="bar-chart">
          <div v-for="cat in data.category_breakdown" :key="cat.category" class="bar-row">
            <span class="bar-label">{{ catName(cat.category) }}</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: barPct(cat.count, maxCatCount) + '%', background: catColor(cat.category) }"></div>
            </div>
            <span class="bar-value">{{ cat.count }}</span>
          </div>
        </div>
      </div>

      <!-- 经理排行 -->
      <div class="panel" v-if="data.manager_ranking.length > 0">
        <div class="panel-title">🏆 经理排行</div>
        <div class="ranking-list">
          <div v-for="(m, idx) in data.manager_ranking" :key="idx" class="ranking-item">
            <span class="rank-num" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
            <span class="rank-name">{{ m.manager_name }}</span>
            <span class="rank-stats">
              线索{{ m.total_leads }} · 转化{{ m.converted_leads }}
            </span>
            <span class="rank-amount" v-if="m.converted_amount > 0">
              {{ formatAmount(m.converted_amount) }}万
            </span>
          </div>
        </div>
      </div>

      <div class="bottom-space"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getLeadDashboard } from '@/api/leads'
import { businessCategoryMap } from '@/utils/format'

const loading = ref(true)
const data = ref<any>({
  total_opportunities: 0,
  total_leads: 0,
  active_leads: 0,
  converted_leads: 0,
  lost_leads: 0,
  conversion_rate: 0,
  total_estimated_amount: 0,
  total_converted_amount: 0,
  category_breakdown: [],
  manager_ranking: [],
})

const maxCatCount = computed(() => {
  return Math.max(...data.value.category_breakdown.map((c: any) => c.count), 1)
})

function funnelPct(value: number, total: number): string {
  if (total === 0) return '5%'
  return Math.max(value / total * 100, 8) + '%'
}

function barPct(value: number, max: number): number {
  return max > 0 ? (value / max * 100) : 0
}

function catName(cat: string): string {
  return businessCategoryMap[cat]?.name || cat
}

function catColor(cat: string): string {
  return businessCategoryMap[cat]?.color || '#999'
}

function formatAmount(val: number): string {
  if (!val) return '0'
  if (val >= 10000) return (val / 10000).toFixed(1) + '亿'
  return val.toFixed(0)
}

onMounted(async () => {
  try {
    const res = await getLeadDashboard()
    data.value = res
  } catch (e) {
    console.error('加载看板失败', e)
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 70px;
}

.page-header {
  background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
  padding: 24px 20px 20px;
  color: #fff;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 4px;
}

.page-subtitle {
  font-size: 12px;
  opacity: 0.8;
  margin: 0;
}

.dashboard-content {
  padding: 12px 16px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #999;
}

/* 指标卡 */
.metric-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.metric-card {
  background: #fff;
  border-radius: 10px;
  padding: 12px 6px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);

  &.highlight {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    .metric-num, .metric-label { color: #fff; }
  }
}

.metric-num {
  font-size: 20px;
  font-weight: 800;
  color: #1a56db;
  line-height: 1.2;
}

.metric-label {
  font-size: 10px;
  color: #9ca3af;
  margin-top: 2px;
}

/* 面板 */
.panel {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}

.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 12px;
}

/* 漏斗 */
.funnel {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
}

.funnel-stage {
  height: 36px;
  background: linear-gradient(90deg, #1a56db, #3b82f6);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  color: #fff;
  transition: width 0.5s ease;

  &:nth-child(2) { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
  &:nth-child(3) { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
  &:nth-child(4) { background: linear-gradient(90deg, #10b981, #34d399); }
}

.funnel-label {
  font-size: 12px;
  font-weight: 600;
}

.funnel-value {
  font-size: 14px;
  font-weight: 800;
}

/* 金额 */
.amount-row {
  display: flex;
  gap: 12px;
}

.amount-item {
  flex: 1;
  text-align: center;
  padding: 10px;
  background: #f9fafb;
  border-radius: 8px;
}

.amount-num {
  font-size: 20px;
  font-weight: 800;

  &.est { color: #f59e0b; }
  &.conv { color: #10b981; }
}

.amount-label {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

/* 柱状图 */
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-label {
  width: 70px;
  font-size: 11px;
  color: #6b7280;
  flex-shrink: 0;
  text-align: right;
}

.bar-track {
  flex: 1;
  height: 18px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.bar-value {
  width: 30px;
  font-size: 12px;
  font-weight: 700;
  color: #374151;
  text-align: right;
}

/* 排行 */
.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 8px;
}

.rank-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: #9ca3af;
  flex-shrink: 0;

  &.rank-1 { background: #f59e0b; }
  &.rank-2 { background: #9ca3af; }
  &.rank-3 { background: #d97706; }
}

.rank-name {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  flex: 1;
}

.rank-stats {
  font-size: 11px;
  color: #6b7280;
}

.rank-amount {
  font-size: 12px;
  font-weight: 700;
  color: #10b981;
}

.bottom-space {
  height: 20px;
}
</style>

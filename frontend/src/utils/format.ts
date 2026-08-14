import dayjs from 'dayjs'

// 格式化日期
export function formatDate(date: string | Date | undefined, format = 'YYYY-MM-DD'): string {
  if (!date) return ''
  return dayjs(date).format(format)
}

// 格式化日期时间
export function formatDateTime(date: string | Date | undefined, format = 'YYYY-MM-DD HH:mm'): string {
  if (!date) return ''
  return dayjs(date).format(format)
}

// 相对时间
export function formatRelativeTime(date: string | Date | undefined): string {
  if (!date) return ''
  const now = dayjs()
  const target = dayjs(date)
  const diffDays = now.diff(target, 'day')

  if (diffDays === 0) {
    const diffHours = now.diff(target, 'hour')
    if (diffHours === 0) {
      const diffMinutes = now.diff(target, 'minute')
      if (diffMinutes === 0) return '刚刚'
      return `${diffMinutes}分钟前`
    }
    return `${diffHours}小时前`
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return formatDate(date)
  }
}

// 行动分类映射（v4新5类）
export const businessCategoryMap: Record<string, { name: string; color: string; icon: string }> = {
  bid_action: { name: '可投标项目', color: '#1a56db', icon: '📑' },
  fin_demand: { name: '融资需求', color: '#f59e0b', icon: '💰' },
  account_chance: { name: '开户结算机会', color: '#10b981', icon: '🏦' },
  park_project: { name: '区域产业动态', color: '#8b5cf6', icon: '🏗️' },
  policy_ref: { name: '监管与政策', color: '#6b7280', icon: '📋' },
}

// 资讯类型映射
export const infoTypeMap: Record<string, { name: string; color: string }> = {
  policy: { name: '政策动态', color: '#3498db' },
  bidding: { name: '招投标', color: '#e67e22' },
  enterprise: { name: '企业动态', color: '#2ecc71' },
  park: { name: '园区动态', color: '#9b59b6' },
}

// 区域标签映射（v3标准7类）
export const areaTagMap: Record<string, string> = {
  chaoyang: '朝阳区',
  dongcheng: '东城区',
  tongzhou: '通州区',
  yizhuang: '亦庄经开区',
  beijing: '北京市级',
  national: '全国性',
  other: '其他地区',
  // 兼容旧标签
  haidian: '海淀区',
  fengtai: '丰台区',
  xicheng: '西城区',
  shijingshan: '石景山区',
  changping: '昌平区',
  daxing: '大兴区',
}

// 行业标签映射（北京主导产业）
export const industryTagMap: Record<string, string> = {
  finance: '金融',
  tech: '科技',
  culture: '文化',
  business_service: '商务服务',
  advanced_manufacturing: '先进制造',
  medical_health: '医药健康',
  digital_economy: '数字经济',
  other: '其他',
  // 兼容旧标签
  manufacturing: '制造业',
  real_estate: '房地产',
  medical: '医药健康',
  education: '教育培训',
  retail: '零售消费',
  logistics: '物流运输',
  energy: '能源环保',
  government: '政府机构',
}

// 线索状态映射
export const leadStatusMap: Record<string, { name: string; color: string }> = {
  new: { name: '新建', color: '#1890ff' },
  active: { name: '跟进中', color: '#52c41a' },
  converted: { name: '已转化', color: '#722ed1' },
  lost: { name: '已流失', color: '#8c8c8c' },
  released: { name: '已释放', color: '#faad14' },
}

// 优先级映射
export const priorityMap: Record<number, { name: string; color: string }> = {
  1: { name: '低', color: '#8c8c8c' },
  2: { name: '中', color: '#faad14' },
  3: { name: '高', color: '#f5222d' },
}

// 数字格式化
export function formatNumber(num: number | undefined): string {
  if (num === undefined || num === null) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 质量分颜色
export function getQualityScoreColor(score: number): string {
  if (score >= 80) return '#52c41a'
  if (score >= 60) return '#faad14'
  return '#f5222d'
}

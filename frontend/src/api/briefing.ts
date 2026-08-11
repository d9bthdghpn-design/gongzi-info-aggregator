import request, { ApiResponse } from './request'

export interface BriefingCategoryItem {
  id: string
  title: string
  summary: string
  business_tip: string
  info_type: string
  quality_score: number
  area_tags: string[]
  industry_tags: string[]
}

export interface BriefingCategory {
  category_code: string
  category_name: string
  icon: string
  count: number
  items: BriefingCategoryItem[]
}

export interface DailyBriefing {
  id: string
  brief_date: string
  area_scope?: string
  content_json: {
    date: string
    total_count: number
    high_value_count: number
    categories: BriefingCategory[]
  }
  total_count: number
  category_counts: Record<string, number>
  is_pushed: boolean
  pushed_at?: string
  created_by?: string
  created_at?: string
}

// 获取今日简报
export function getTodayBriefing(): Promise<ApiResponse<DailyBriefing>> {
  return request.get('/briefings/today')
}

// 按日期获取简报
export function getBriefingByDate(date: string): Promise<ApiResponse<DailyBriefing>> {
  return request.get(`/briefings/${date}`)
}

// 生成简报
export function generateBriefing(date: string, areaScope?: string): Promise<ApiResponse<DailyBriefing>> {
  return request.post('/briefings/generate', {
    brief_date: date,
    area_scope: areaScope,
  })
}

// 推送简报
export function pushBriefing(id: string): Promise<ApiResponse<DailyBriefing>> {
  return request.post(`/briefings/${id}/push`)
}

// 获取最近的简报列表
export function getRecentBriefings(limit = 7): Promise<ApiResponse<DailyBriefing[]>> {
  return request.get('/briefings/list/recent', { params: { limit } })
}

import request, { ApiResponse, PageResponse } from './request'

export interface NewsItem {
  id: string
  title: string
  content_summary?: string
  content_raw?: string
  business_category?: string
  area_tags: string[]
  industry_tags: string[]
  topic_tags?: string[]  // 主题标签（v5）
  info_type?: string
  source_type?: string
  source_channel?: string
  source_url?: string
  publish_date?: string
  business_tip?: string
  quality_score: number
  score_dimensions?: Record<string, number>  // 7维评分明细
  event_cluster_id?: string  // 事件聚类ID
  status: string
  view_count: number
  lead_count: number
  created_at?: string
}

export interface EventCluster {
  id: string
  title: string
  description?: string
  event_type?: string
  news_count: number
  news_ids: string[]
  source_channels: string[]
  first_publish_date?: string
  last_publish_date?: string
  max_quality_score: number
  created_at?: string
}

export interface EventClusterDetail extends EventCluster {
  news_items: NewsItem[]
}

export interface NewsStats {
  today_new: number
  bidding_count: number
  policy_count: number
  enterprise_count: number
  high_value_count: number
  today_new_trend: number
  last_updated?: string
  total?: number
  bid_action_count?: number
  fin_demand_count?: number
  account_chance_count?: number
  park_project_count?: number
  policy_ref_count?: number
}

export interface TagInfo {
  code: string
  name: string
  color?: string
}

export interface TopicInfo {
  id: string
  title: string
  description?: string
  cover_image?: string
  filter_config: Record<string, any>
  sort_order: number
  is_active: boolean
  total_count?: number
  month_new_count?: number
  high_value_count?: number
}

export interface NewsQueryParams {
  page?: number
  page_size?: number
  keyword?: string
  business_category?: string
  action_category?: string
  info_type?: string
  status?: string
  area_tags?: string  // 逗号分隔，如 chaoyang,dongcheng
  industry_tags?: string  // 逗号分隔，如 tech,finance
  min_quality_score?: number
  start_date?: string
  end_date?: string
  date_range?: string  // 快捷时间范围：7d/1m/3m/6m
  sort_by?: string
  sort_order?: string
}

// 获取资讯统计
export function getNewsStats(): Promise<ApiResponse<NewsStats>> {
  return request.get('/news/stats')
}

// 获取资讯列表
export function getNewsList(params: NewsQueryParams): Promise<PageResponse<NewsItem>> {
  return request.get('/news', { params })
}

// 获取资讯详情
export function getNewsDetail(id: string): Promise<ApiResponse<NewsItem>> {
  return request.get(`/news/${id}`)
}

// 更新资讯
export function updateNews(id: string, data: any): Promise<ApiResponse<NewsItem>> {
  return request.put(`/news/${id}`, data)
}

// 审核资讯
export function auditNews(id: string, status: string, comment?: string): Promise<ApiResponse<NewsItem>> {
  return request.post(`/news/${id}/audit`, null, {
    params: { status, comment },
  })
}

// 获取所有标签
export function getAllTags(): Promise<ApiResponse<Record<string, TagInfo[]>>> {
  return request.get('/news/tags/all')
}

// 按类型获取标签
export function getTagsByType(tagType: string): Promise<ApiResponse<TagInfo[]>> {
  return request.get(`/news/tags/${tagType}`)
}

// 获取专题列表
export function getTopics(): Promise<ApiResponse<TopicInfo[]>> {
  return request.get('/news/topics/list')
}

// 获取专题下的资讯
export function getTopicNews(
  topicId: string,
  page = 1,
  pageSize = 20
): Promise<PageResponse<NewsItem>> {
  return request.get(`/news/topics/${topicId}/news`, {
    params: { page, page_size: pageSize },
  })
}

// 获取事件聚类列表
export function getEventClusters(
  page = 1,
  pageSize = 20
): Promise<PageResponse<EventCluster>> {
  return request.get('/news/events', {
    params: { page, page_size: pageSize },
  })
}

// 获取事件聚类详情
export function getEventClusterDetail(clusterId: string): Promise<ApiResponse<EventClusterDetail>> {
  return request.get(`/news/events/${clusterId}`)
}

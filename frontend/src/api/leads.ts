import request, { ApiResponse, PageResponse } from './request'

export interface LeadItem {
  id: string
  company_name: string
  credit_code?: string
  industry?: string
  area?: string
  contact_person?: string
  contact_title?: string
  contact_phone?: string
  intent_business: string[]
  project_desc?: string
  expected_date?: string
  lead_source?: string
  source_news_id?: string
  priority: number
  status: string
  reporter_id?: string
  assignee_id?: string
  public_pool: boolean
  protect_expire_at?: string
  last_followup_time?: string
  next_followup_time?: string
  created_at?: string
  updated_at?: string
}

export interface LeadFollowup {
  id: string
  lead_id: string
  followup_type: string
  content: string
  next_action?: string
  next_time?: string
  follower_id: string
  followup_time: string
  attachments: string[]
  created_at?: string
}

export interface LeadQueryParams {
  page?: number
  page_size?: number
  keyword?: string
  industry?: string
  area?: string
  status?: string
  priority?: number
  public_pool?: boolean
  sort_by?: string
  sort_order?: string
}

// 获取线索列表
export function getLeadList(params: LeadQueryParams): Promise<PageResponse<LeadItem>> {
  return request.get('/leads', { params })
}

// 获取我的线索
export function getMyLeads(page = 1, pageSize = 20): Promise<PageResponse<LeadItem>> {
  return request.get('/leads/mine', { params: { page, page_size: pageSize } })
}

// 获取公海池线索
export function getPublicPoolLeads(
  page = 1,
  pageSize = 20,
  keyword?: string
): Promise<PageResponse<LeadItem>> {
  return request.get('/leads/public-pool', {
    params: { page, page_size: pageSize, keyword },
  })
}

// 获取线索详情
export function getLeadDetail(id: string): Promise<ApiResponse<LeadItem>> {
  return request.get(`/leads/${id}`)
}

// 创建线索
export function createLead(data: any): Promise<ApiResponse<LeadItem>> {
  return request.post('/leads', data)
}

// 更新线索
export function updateLead(id: string, data: any): Promise<ApiResponse<LeadItem>> {
  return request.put(`/leads/${id}`, data)
}

// 领取线索
export function claimLead(id: string, protectDays = 30): Promise<ApiResponse<LeadItem>> {
  return request.post(`/leads/${id}/claim`, null, {
    params: { protect_days: protectDays },
  })
}

// 释放线索
export function releaseLead(id: string): Promise<ApiResponse<LeadItem>> {
  return request.post(`/leads/${id}/release`)
}

// 分配线索
export function assignLead(id: string, assigneeId: string, protectDays = 30): Promise<ApiResponse<LeadItem>> {
  return request.post(`/leads/${id}/assign`, {
    assignee_id: assigneeId,
    protect_days: protectDays,
  })
}

// 获取跟进记录
export function getLeadFollowups(
  leadId: string,
  page = 1,
  pageSize = 20
): Promise<PageResponse<LeadFollowup>> {
  return request.get(`/leads/${leadId}/followups`, {
    params: { page, page_size: pageSize },
  })
}

// 添加跟进记录
export function addLeadFollowup(leadId: string, data: any): Promise<ApiResponse<LeadFollowup>> {
  return request.post(`/leads/${leadId}/followups`, data)
}

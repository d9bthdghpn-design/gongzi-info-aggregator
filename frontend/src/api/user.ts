import request, { ApiResponse } from './request'

export interface UserInfo {
  id: string
  username: string
  email?: string
  phone?: string
  full_name?: string
  avatar_url?: string
  department?: string
  position?: string
  role: string
  is_active: boolean
  last_login_at?: string
  created_at?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

// 登录
export function login(username: string, password: string): Promise<ApiResponse<TokenResponse>> {
  return request.post('/auth/login', { username, password })
}

// 刷新Token
export function refreshToken(refreshToken: string): Promise<ApiResponse<TokenResponse>> {
  return request.post('/auth/refresh', { refresh_token: refreshToken })
}

// 获取当前用户信息
export function getCurrentUser(): Promise<ApiResponse<UserInfo>> {
  return request.get('/auth/me')
}

// 获取用户列表
export function getUserList(): Promise<ApiResponse<UserInfo[]>> {
  return request.get('/users')
}

// 创建用户
export function createUser(data: any): Promise<ApiResponse<UserInfo>> {
  return request.post('/users', data)
}

// 更新用户
export function updateUser(userId: string, data: any): Promise<ApiResponse<UserInfo>> {
  return request.put(`/users/${userId}`, data)
}

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { useUserStore } from '@/store/user'
import { showToast } from 'vant'

const service: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    return res
  },
  async (error) => {
    const userStore = useUserStore()

    if (error.response?.status === 401) {
      // Token过期，尝试刷新
      const refreshed = await userStore.tryRefreshToken()
      if (refreshed) {
        // 重新请求
        const config = error.config
        config.headers.Authorization = `Bearer ${userStore.token}`
        return service(config)
      } else {
        showToast('登录已过期，请重新登录')
        // 跳转到登录页
        window.location.href = '/login'
      }
    } else if (error.response?.status === 403) {
      showToast('没有权限访问')
    } else if (error.response?.status >= 500) {
      showToast('服务器错误，请稍后重试')
    } else {
      showToast(error.response?.data?.message || '请求失败')
    }

    return Promise.reject(error)
  }
)

export default service

// 通用响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  total?: number
  page?: number
  page_size?: number
  total_pages?: number
}

// 分页响应类型
export interface PageResponse<T = any> extends ApiResponse<T[]> {
  total: number
  page: number
  page_size: number
  total_pages: number
}

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, refreshToken as refreshTokenApi, getCurrentUser } from '@/api/user'
import type { UserInfo, TokenResponse } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  async function login(username: string, password: string): Promise<boolean> {
    try {
      const res = await loginApi(username, password)
      if (res.code === 0 && res.data) {
        setToken(res.data.access_token, res.data.refresh_token)
        userInfo.value = res.data.user
        return true
      }
      return false
    } catch (error) {
      console.error('登录失败:', error)
      return false
    }
  }

  function setToken(accessToken: string, refresh: string) {
    token.value = accessToken
    refreshToken.value = refresh
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refresh)
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  async function checkAuth() {
    if (token.value) {
      try {
        const res = await getCurrentUser()
        if (res.code === 0 && res.data) {
          userInfo.value = res.data
        }
      } catch (error) {
        // Token过期，尝试刷新
        await tryRefreshToken()
      }
    }
  }

  async function tryRefreshToken(): Promise<boolean> {
    if (!refreshToken.value) return false

    try {
      const res = await refreshTokenApi(refreshToken.value)
      if (res.code === 0 && res.data) {
        setToken(res.data.access_token, res.data.refresh_token)
        userInfo.value = res.data.user
        return true
      }
    } catch (error) {
      console.error('刷新Token失败:', error)
    }

    logout()
    return false
  }

  return {
    token,
    refreshToken,
    userInfo,
    isLoggedIn,
    isAdmin,
    login,
    logout,
    checkAuth,
    tryRefreshToken,
  }
})

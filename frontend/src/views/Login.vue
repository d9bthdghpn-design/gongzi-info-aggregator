<template>
  <div class="login-page">
    <div class="login-header">
      <div class="logo">🏦</div>
      <h1 class="app-title">对公资讯聚合系统</h1>
      <p class="app-subtitle">智能监测 · 商机挖掘 · 高效营销</p>
    </div>

    <div class="login-form">
      <div class="form-item">
        <span class="form-icon">👤</span>
        <input
          v-model="username"
          type="text"
          placeholder="请输入用户名"
          @keyup.enter="handleLogin"
        />
      </div>

      <div class="form-item">
        <span class="form-icon">🔒</span>
        <input
          v-model="password"
          type="password"
          placeholder="请输入密码"
          @keyup.enter="handleLogin"
        />
      </div>

      <button
        class="login-btn"
        :class="{ disabled: loading }"
        :disabled="loading"
        @click="handleLogin"
      >
        <van-loading v-if="loading" type="spinner" size="20px" color="#fff" />
        <span v-else>登 录</span>
      </button>

      <div class="login-tips">
        <span>默认账号：admin / admin123</span>
      </div>
    </div>

    <div class="login-footer">
      <p>© 2024 对公资讯聚合系统</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const username = ref('admin')
const password = ref('admin123')
const loading = ref(false)

async function handleLogin() {
  if (!username.value) {
    showToast('请输入用户名')
    return
  }
  if (!password.value) {
    showToast('请输入密码')
    return
  }

  loading.value = true
  try {
    const success = await userStore.login(username.value, password.value)
    if (success) {
      showToast('登录成功')
      const redirect = route.query.redirect as string || '/home'
      router.replace(redirect)
    } else {
      showToast('用户名或密码错误')
    }
  } catch (error) {
    showToast('登录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #1a56db 0%, #1e40af 50%, #f5f7fa 50%);
  display: flex;
  flex-direction: column;
  padding: 0 24px;
  padding-top: env(safe-area-inset-top);
}

.login-header {
  text-align: center;
  padding: 60px 0 40px;
  color: #fff;

  .logo {
    font-size: 64px;
    margin-bottom: 16px;
  }

  .app-title {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 8px;
  }

  .app-subtitle {
    font-size: 14px;
    opacity: 0.8;
  }
}

.login-form {
  background-color: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.form-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 12px;
  margin-bottom: 16px;

  .form-icon {
    font-size: 18px;
    margin-right: 12px;
  }

  input {
    flex: 1;
    border: none;
    background: transparent;
    font-size: 15px;
    color: #262626;
    outline: none;

    &::placeholder {
      color: #bfbfbf;
    }
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;

  &:active {
    transform: scale(0.98);
  }

  &.disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

.login-tips {
  text-align: center;
  margin-top: 16px;
  font-size: 12px;
  color: #8c8c8c;
}

.login-footer {
  margin-top: auto;
  padding: 20px 0;
  text-align: center;
  font-size: 12px;
  color: #bfbfbf;
  padding-bottom: calc(20px + env(safe-area-inset-bottom));
}
</style>

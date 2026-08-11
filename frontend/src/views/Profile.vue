<template>
  <div class="profile-page page-container">
    <!-- 顶部Header -->
    <div class="page-header">
      <div class="user-info">
        <div class="avatar">
          <span v-if="userStore.userInfo?.avatar_url">
            <img :src="userStore.userInfo.avatar_url" alt="avatar" />
          </span>
          <span v-else class="avatar-placeholder">
            {{ userStore.userInfo?.full_name?.charAt(0) || userStore.userInfo?.username?.charAt(0) || 'U' }}
          </span>
        </div>
        <div class="user-detail">
          <div class="user-name">{{ userStore.userInfo?.full_name || userStore.userInfo?.username }}</div>
          <div class="user-dept">{{ userStore.userInfo?.department || '-' }} · {{ userStore.userInfo?.position || '-' }}</div>
        </div>
      </div>
    </div>

    <!-- 数据统计 -->
    <div class="stats-card">
      <div class="stat-item">
        <div class="stat-num">{{ myStats.totalLeads }}</div>
        <div class="stat-label">我的线索</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{{ myStats.following }}</div>
        <div class="stat-label">跟进中</div>
      </div>
      <div class="stat-item">
        <div class="stat-num converted">{{ myStats.converted }}</div>
        <div class="stat-label">已转化</div>
      </div>
    </div>

    <!-- 功能菜单 -->
    <div class="menu-list">
      <div class="menu-group">
        <div class="menu-item" @click="goTo('/leads')">
          <span class="menu-icon">🎯</span>
          <span class="menu-text">我的线索</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item" @click="goTo('/briefing')">
          <span class="menu-icon">📰</span>
          <span class="menu-text">每日简报</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item" @click="goTo('/topics')">
          <span class="menu-icon">📋</span>
          <span class="menu-text">业务专题</span>
          <span class="menu-arrow">›</span>
        </div>
      </div>

      <div class="menu-group" v-if="userStore.isAdmin">
        <div class="menu-title">管理功能</div>
        <div class="menu-item" @click="goToAdmin('audit')">
          <span class="menu-icon">✅</span>
          <span class="menu-text">资讯审核</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item" @click="goToAdmin('sources')">
          <span class="menu-icon">🕷️</span>
          <span class="menu-text">采集渠道</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item" @click="goToAdmin('users')">
          <span class="menu-icon">👥</span>
          <span class="menu-text">用户管理</span>
          <span class="menu-arrow">›</span>
        </div>
      </div>

      <div class="menu-group">
        <div class="menu-title">设置</div>
        <div class="menu-item" @click="showSettings">
          <span class="menu-icon">⚙️</span>
          <span class="menu-text">系统设置</span>
          <span class="menu-arrow">›</span>
        </div>
        <div class="menu-item" @click="showAbout">
          <span class="menu-icon">ℹ️</span>
          <span class="menu-text">关于我们</span>
          <span class="menu-arrow">›</span>
        </div>
      </div>
    </div>

    <!-- 退出登录 -->
    <div class="logout-section">
      <button class="logout-btn" @click="handleLogout">退出登录</button>
    </div>

    <!-- 底部TabBar -->
    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { useUserStore } from '@/store/user'
import TabBar from '@/components/TabBar.vue'

const router = useRouter()
const userStore = useUserStore()

const myStats = reactive({
  totalLeads: 0,
  following: 0,
  converted: 0,
})

function goTo(path: string) {
  router.push(path)
}

function goToAdmin(type: string) {
  showToast('管理功能开发中')
}

function showSettings() {
  showToast('设置功能开发中')
}

function showAbout() {
  showToast('对公资讯聚合系统 v1.0.0')
}

async function handleLogout() {
  try {
    await showConfirmDialog({
      title: '确认退出',
      message: '确定要退出登录吗？',
    })

    userStore.logout()
    router.push('/login')
  } catch (error) {
    // 用户取消
  }
}
</script>

<style lang="scss" scoped>
.profile-page {
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #1a2942 0%, #2c3e5a 100%);
  color: #fff;
  padding: 30px 16px 60px;
  padding-top: calc(30px + env(safe-area-inset-top));
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .avatar-placeholder {
    font-size: 28px;
    font-weight: 600;
  }
}

.user-detail {
  flex: 1;

  .user-name {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  .user-dept {
    font-size: 13px;
    opacity: 0.8;
  }
}

.stats-card {
  display: flex;
  background-color: #fff;
  margin: -40px 16px 16px;
  border-radius: 12px;
  padding: 20px 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  position: relative;
  z-index: 10;
}

.stat-item {
  flex: 1;
  text-align: center;

  .stat-num {
    font-size: 24px;
    font-weight: 700;
    color: #1a2942;
    margin-bottom: 4px;

    &.converted {
      color: #52c41a;
    }
  }

  .stat-label {
    font-size: 12px;
    color: #8c8c8c;
  }
}

.menu-list {
  padding: 0 12px;
}

.menu-group {
  background-color: #fff;
  border-radius: 12px;
  margin-bottom: 12px;
  overflow: hidden;
}

.menu-title {
  padding: 12px 16px 8px;
  font-size: 12px;
  color: #8c8c8c;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background-color: #fafafa;
  }

  .menu-icon {
    font-size: 20px;
    margin-right: 12px;
  }

  .menu-text {
    flex: 1;
    font-size: 15px;
    color: #262626;
  }

  .menu-arrow {
    font-size: 18px;
    color: #bfbfbf;
  }
}

.logout-section {
  padding: 20px 16px 40px;
}

.logout-btn {
  width: 100%;
  height: 44px;
  background-color: #fff;
  border: none;
  border-radius: 22px;
  font-size: 15px;
  color: #f5222d;
  cursor: pointer;

  &:active {
    background-color: #fafafa;
  }
}
</style>

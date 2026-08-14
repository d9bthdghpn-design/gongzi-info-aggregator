import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/home',
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页', requiresAuth: true, tabBar: true },
  },
  {
    path: '/topics',
    name: 'Topics',
    component: () => import('@/views/Topics.vue'),
    meta: { title: '专题', requiresAuth: true, tabBar: true },
  },
  {
    path: '/briefing',
    name: 'Briefing',
    component: () => import('@/views/Briefing.vue'),
    meta: { title: '简报', requiresAuth: true, tabBar: true },
  },
  // 线索相关路由已隐藏（后端保留，前端暂不展示）
  // {
  //   path: '/leads',
  //   name: 'Leads',
  //   component: () => import('@/views/Leads.vue'),
  //   meta: { title: '线索', requiresAuth: true, tabBar: true },
  // },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '我的', requiresAuth: true, tabBar: true },
  },
  {
    path: '/news/:id',
    name: 'NewsDetail',
    component: () => import('@/views/NewsDetail.vue'),
    meta: { title: '资讯详情', requiresAuth: true },
  },
  // {
  //   path: '/leads/create',
  //   name: 'LeadCreate',
  //   component: () => import('@/views/LeadCreate.vue'),
  //   meta: { title: '线索上报', requiresAuth: true },
  // },
  // {
  //   path: '/leads/:id',
  //   name: 'LeadDetail',
  //   component: () => import('@/views/LeadDetail.vue'),
  //   meta: { title: '线索详情', requiresAuth: true },
  // },
  {
    path: '/topics/:id',
    name: 'TopicDetail',
    component: () => import('@/views/TopicDetail.vue'),
    meta: { title: '专题详情', requiresAuth: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '转化看板', requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router

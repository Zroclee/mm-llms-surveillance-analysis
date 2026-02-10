import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

/**
 * 定义路由表
 * 包含 Home, Monitor, House 三个主要页面
 */
const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: {
      title: '首页'
    }
  },
  {
    path: '/monitor',
    name: 'Monitor',
    component: () => import('../views/Monitor.vue'),
    meta: {
      title: '监控'
    }
  },
  {
    path: '/house',
    name: 'House',
    component: () => import('../views/House.vue'),
    meta: {
      title: '房源'
    }
  }
]

/**
 * 创建路由实例
 * 使用 WebHistory 模式
 */
const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

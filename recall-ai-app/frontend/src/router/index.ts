/** Vue Router 配置:页面路由(hash 模式,兼容静态文件直接打开)。 */
import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/questions' },
    {
      path: '/questions',
      name: 'questions',
      component: () => import('@/views/QuestionsView.vue'),
      meta: { title: '错题集' },
    },
    {
      path: '/ai',
      name: 'ai',
      component: () => import('@/views/AIView.vue'),
      meta: { title: 'AI 答疑' },
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: () => import('@/views/AnalyticsView.vue'),
      meta: { title: '数据看板' },
    },
    {
      path: '/help',
      name: 'help',
      component: () => import('@/views/HelpView.vue'),
      meta: { title: '帮助' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: '设置' },
    },
  ],
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? '')} · Recall AI`
})

export default router

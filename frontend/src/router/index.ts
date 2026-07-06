import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'simulation',
      component: () => import('@/pages/SimulationPage.vue'),
    },
    {
      path: '/benchmark',
      name: 'benchmark',
      component: () => import('@/pages/BenchmarkPage.vue'),
    },
    {
      path: '/datasets',
      name: 'datasets',
      component: () => import('@/pages/DatasetsPage.vue'),
    },
    {
      path: '/pipelines',
      name: 'pipelines',
      component: () => import('@/pages/PipelinesPage.vue'),
    },
    {
      path: '/models',
      name: 'models',
      component: () => import('@/pages/ModelsPage.vue'),
    },
  ],
})

export default router

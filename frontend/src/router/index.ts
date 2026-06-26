import { createRouter, createWebHistory } from 'vue-router'
import SimulationPage from '../views/SimulationPage.vue'
import ResourcesView from '../views/ResourcesView.vue'
import BenchmarkView from '../views/BenchmarkView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/simulation',
      name: 'simulation',
      component: SimulationPage,
    },
    {
      path: '/resources',
      name: 'resources',
      component: ResourcesView,
    },
    {
      path: '/benchmark',
      name: 'benchmark',
      component: BenchmarkView,
    },
  ],
})

export default router

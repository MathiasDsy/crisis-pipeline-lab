import { createRouter, createWebHistory } from 'vue-router'
import DashboardMap from '../views/DashboardMap.vue'
import PipelineLab from '../views/TweetsDashboard.vue'
import EventsDashboard from '../views/EventsDashboard.vue'
import BenchmarkPage  from '../views/BenchmarkPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: DashboardMap,
    },
    {
      path: '/tweets',
      name: 'tweets',
      component: PipelineLab,
    },
    {
      path: '/events',
      name: 'events',
      component: EventsDashboard,
    },
    {
      path: '/benchmarks',
      name: 'benchmarks',
      component: BenchmarkPage
    }
  ],
})

export default router

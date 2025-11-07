import { createRouter, createWebHistory } from 'vue-router'

// Global website pages
import HomeView from './views/HomeView.vue'
import PriceView from './views/PriceView.vue'
import AboutView from './views/AboutView.vue'
import DemoView from './views/DemoView.vue'

// Phone app subviews
import MapView from './views/MapView.vue'
import ExploreView from './views/ExploreView.vue'
import ProfileView from './views/ProfileView.vue'

const routes = [
  { path: '/', redirect: '/what-is-minutetour' },
  { path: '/what-is-minutetour', component: HomeView },
  { path: '/vision', component: PriceView },
  { path: '/about-us', component: AboutView },
  {
    path: '/app-demo',
    component: DemoView,
    children: [
      { path: '', redirect: '/app-demo/map' },
      { path: 'map', component: MapView },
      { path: 'explore', component: ExploreView },
      { path: 'profile', component: ProfileView }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // If there's a saved position (e.g., browser back button), use it
    if (savedPosition) {
      return savedPosition
    }
    // Otherwise, scroll to top
    return { top: 0, behavior: 'smooth' }
  }
})

export default router

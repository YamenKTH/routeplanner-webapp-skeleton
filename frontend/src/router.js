import { createRouter, createWebHistory } from 'vue-router'

// Global website pages
import HomeView from './views/HomeView.vue'
import VisionView from './views/VisionView.vue'
import AboutView from './views/AboutView.vue'
import DemoView from './views/DemoView.vue'

// Phone app subviews
import MapView from './views/mapview/MapView.vue'
import ExploreView from './views/ExploreView.vue'
import ProfileView from './views/ProfileView.vue'

const routes = [
  { path: '/', redirect: '/what-is-x' },
  { path: '/what-is-x', component: HomeView },
  { path: '/vision', component: VisionView },
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

export default createRouter({
  history: createWebHistory(),
  routes
})

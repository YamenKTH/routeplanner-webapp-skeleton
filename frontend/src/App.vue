<template>
  <div class="site-wrapper">
    <TopNav />
    <router-view />
  </div>
</template>

<script setup>
import TopNav from './components/TopNav.vue'
</script>

<style>
body, html {
  margin: 0;
  padding: 0;
  height: 100%;
  background: #f7f7f7;
}
.site-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
</style>

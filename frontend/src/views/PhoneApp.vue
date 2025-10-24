<template>
  <div class="phone-app">
    <router-view class="phone-view" />
    <BottomNav />
  </div>
</template>

<script setup>
import BottomNav from '../components/BottomNav.vue'
</script>

<style>
.phone-app {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.phone-view {
  flex: 1;
  overflow: hidden;
}
</style>

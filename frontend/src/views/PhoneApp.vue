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

.phone-view {
  flex: 1;
  overflow: auto;
  border-radius: 20px;
}
.phone-app {
  display: flex;
  padding:relative;
  flex-direction: column;
  height: 100%;
  width: 100%;
  border: 13px solid #000000;
  z-index: 1001;
  border-radius: 33px;
}


</style>

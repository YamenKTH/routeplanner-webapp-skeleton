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
  height: 99%;            /* 100% looks good on browser. 99% works for phone (because you can scroll down and hide safari search bar*/ 
}
.phone-view {
  flex: 1;
  overflow: hidden;
}
</style>

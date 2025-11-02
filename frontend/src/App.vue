<template>
  <div class="phone-app">
    <router-view class="phone-view" />
  </div>
</template>

<script setup>
// No BottomNav import needed for now
</script>

<style>
.phone-app {
  display: flex;
  flex-direction: column;
  /* 👇 important: small scroll area to hide Safari bars */
  height: 101vh;
  overflow-y: scroll;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

.phone-view {
  flex: 1;
  overflow: hidden;
}
</style>
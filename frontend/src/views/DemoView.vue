<template>
  <div class="demo-wrapper">
    <div class="phone-frame">
      <PhoneApp />
    </div>
  </div>
</template>

<script setup>
import PhoneApp from './PhoneApp.vue'
</script>

<style>
.demo-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f3f3f3;
  height: calc(100vh - 64px); /* leave space for top bar */
}
.phone-frame {
  width: 420px;
  height: 90vh;
  background: white;
  border-radius: 28px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.3);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border-radius: 33px;
}
</style>

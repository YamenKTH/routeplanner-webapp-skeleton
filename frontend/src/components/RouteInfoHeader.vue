<template>
  <div class="route-info-header-top">
    <div class="route-info-content">
      <div class="route-direction">
        <span class="direction-icon-large">{{ direction }}</span>
        <div class="direction-details">
          <div class="route-place">{{ place }}</div>
          <div class="route-distance">{{ distance || '--' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  direction: {
    type: String,
    default: '➡️',
  },
  place: {
    type: String,
    default: '',
  },
  distance: {
    type: String,
    default: null,
  },
});
</script>

<style scoped>
.route-info-header-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1001;
  background: linear-gradient(135deg, rgba(106, 92, 255, 0.95) 0%, rgba(255, 61, 179, 0.95) 100%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  padding: 16px 20px;
}

.route-info-content {
  max-width: 90%;
  margin: 0 auto;
}

.route-direction {
  display: flex;
  align-items: center;
  gap: 16px;
}

.direction-icon-large {
  font-size: 3rem;
  flex-shrink: 0;
  line-height: 1;
}

.direction-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.route-place {
  font-weight: 700;
  font-size: 1.2rem;
  color: #ffffff;
  line-height: 1.3;
}

.route-distance {
  font-size: 1rem;
  font-weight: 600;
  opacity: 0.95;
  color: #ffffff;
}
</style>


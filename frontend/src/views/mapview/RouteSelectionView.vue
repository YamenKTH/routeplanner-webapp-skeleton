<template>
  <div>
    <!-- Route selection -->
    <div class="route-selection">
      <div class="route-nav">
        <button 
          class="route-nav-btn" 
          @click="handlePrevRoute" 
          :disabled="currentRouteIndex === 0"
        >
          ⬅️
        </button>
        <span class="route-counter">Route {{ currentRouteIndex + 1 }} / {{ generatedRoutes.length }}</span>
        <button 
          class="route-nav-btn" 
          @click="handleNextRoute" 
          :disabled="currentRouteIndex === generatedRoutes.length - 1"
        >
          ➡️
        </button>
      </div>
      <button class="confirm-route-btn" @click="handleConfirmRoute">Confirm This Route</button>
    </div>

    <!-- Route stats -->
    <div v-if="currentRoute" class="route-stats">
      <div class="stat-item">
        <span class="stat-icon">📍</span>
        <span class="stat-value">{{ currentRoute.stops?.length || 0 }} stops</span>
      </div>
      <div class="stat-item">
        <span class="stat-icon">📏</span>
        <span class="stat-value">{{ currentRoute.distance || 'N/A' }} km</span>
      </div>
      <div class="stat-item">
        <span class="stat-icon">🕒</span>
        <span class="stat-value">{{ currentRoute.time || 'N/A' }}</span>
      </div>
    </div>

    <!-- POI List -->
    <div class="poi-list-container">
      <h4 class="poi-list-title">Route Stops</h4>
      <div class="poi-list">
        <div 
          v-for="(stop, index) in currentRoute.stops" 
          :key="index"
          class="poi-item"
          :class="{ 
            'start-stop': stop.is_start,
            'end-stop': stop.is_end
          }"
        >
          <div class="poi-number" :class="{ 'start-end-icon': stop.is_start || stop.is_end }">
            <span v-if="stop.is_start">🚩</span>
            <span v-else-if="stop.is_end">🏁</span>
            <span v-else>{{ index }}</span>
          </div>
          <div class="poi-info">
            <div class="poi-header">
              <div class="poi-name">{{ getStopName(stop, index) }}</div>
              <span v-if="stop.is_start" class="stop-badge start-badge">Start</span>
              <span v-else-if="stop.is_end" class="stop-badge end-badge">End</span>
            </div>
            <div v-if="stop.kinds && stop.kinds.length > 0" class="poi-kinds">
              {{ stop.kinds.slice(0, 3).join(", ") }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Cancel Route Button (at bottom) -->
    <button class="cancel-route-btn" @click="handleCancelRoute">❌ Cancel Route</button>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  generatedRoutes: {
    type: Array,
    required: true,
  },
  currentRouteIndex: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits([
  'prev-route',
  'next-route',
  'confirm-route',
  'cancel-route',
]);

function handlePrevRoute() {
  emit('prev-route');
}

function handleNextRoute() {
  emit('next-route');
}

function handleConfirmRoute() {
  emit('confirm-route');
}

function handleCancelRoute() {
  emit('cancel-route');
}

const currentRoute = computed(() => {
  if (props.generatedRoutes.length === 0 || props.currentRouteIndex < 0) return null;
  return props.generatedRoutes[props.currentRouteIndex];
});

function getStopName(stop, index) {
  if (stop.is_start) return "Start Point";
  if (stop.is_end) return "End Point";
  return stop.name || `Stop ${index + 1}`;
}
</script>

<style scoped>
/* Route Selection */
.route-selection {
  background: rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 12px;
}

.route-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.route-nav-btn {
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.3);
  color: #eef4ff;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.route-nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.route-counter {
  font-weight: bold;
}

.confirm-route-btn {
  width: 100%;
  background: linear-gradient(135deg, #00c853 0%, #64dd17 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px;
  font-weight: bold;
  cursor: pointer;
}

/* Cancel Route Button */
.cancel-route-btn {
  width: 100%;
  margin-top: 12px;
  background: rgba(255, 61, 61, 0.2);
  border: 1px solid rgba(255, 61, 61, 0.4);
  color: #ff6b6b;
  padding: 10px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  font-size: 0.9rem;
}

.cancel-route-btn:hover {
  background: rgba(255, 61, 61, 0.3);
}

/* Route Stats */
.route-stats {
  display: flex;
  justify-content: space-around;
  background: rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-icon {
  font-size: 1.2rem;
}

.stat-value {
  font-size: 0.85rem;
  font-weight: 600;
}

/* POI List */
.poi-list-container {
  background: rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.poi-list-title {
  margin: 0 0 12px 0;
  font-size: 1rem;
  font-weight: bold;
}

.poi-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.poi-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  border: 1px solid transparent;
}

.poi-item.start-stop {
  border-left: 3px solid #00c853;
}

.poi-item.end-stop {
  border-left: 3px solid #ff3db3;
}

.poi-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.poi-number.start-end-icon {
  background: rgba(106, 92, 255, 0.3);
  font-size: 1.1rem;
}

.poi-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.poi-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.poi-name {
  font-weight: 600;
  font-size: 0.95rem;
}

.stop-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: bold;
}

.start-badge {
  background: rgba(0, 200, 83, 0.3);
  color: #00c853;
}

.end-badge {
  background: rgba(255, 61, 179, 0.3);
  color: #ff3db3;
}

.poi-kinds {
  font-size: 0.75rem;
  opacity: 0.8;
  color: #d9e6ff;
}

.poi-list-container::-webkit-scrollbar {
  width: 6px;
}

.poi-list-container::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.05);
  border-radius: 3px;
}

.poi-list-container::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.2);
  border-radius: 3px;
}
</style>


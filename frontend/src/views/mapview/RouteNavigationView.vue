<template>
  <div class="route-navigation-view">
    <!-- Current Stop Details -->
    <div class="current-stop-card">
      <div v-if="currentStop" class="stop-info">
        <div class="stop-header">
          <div class="stop-name-large">{{ getStopName(currentStop, currentPoiIndex) }}</div>
          <span v-if="currentStop.is_start" class="stop-badge start-badge">Start</span>
          <span v-else-if="currentStop.is_end" class="stop-badge end-badge">End</span>
          <span v-else class="stop-number">Stop {{ currentPoiIndex + 1 }}</span>
        </div>
        
        <!-- Categories/Kinds -->
        <div v-if="currentStop.kinds && currentStop.kinds.length > 0" class="stop-kinds">
          {{ currentStop.kinds.slice(0, 3).join(", ") }}
        </div>
        
        <!-- Rating and Score -->
        <div v-if="currentStop.raw_rate || currentStop.score" class="stop-metrics">
          <span v-if="currentStop.raw_rate" class="rating">
            ⭐ {{ currentStop.raw_rate }}
          </span>
          <span v-if="currentStop.score" class="score">
            Score: {{ Math.round(currentStop.score) }}
          </span>
        </div>
        
        <!-- Wikipedia Description -->
        <div v-if="currentStop.det?.wikipedia_extracts?.text" class="stop-description">
          {{ truncateText(currentStop.det.wikipedia_extracts.text, 150) }}
        </div>
        
        <!-- Wikipedia Views -->
        <div v-if="currentStop.wv?.views_365" class="stop-wiki-info">
          📖 {{ formatNumber(currentStop.wv.views_365) }} views
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
  confirmedRoute: {
    type: Object,
    required: true,
  },
  currentPoiIndex: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits([
  'prev-poi',
  'next-poi',
  'poi-click',
  'cancel-route',
]);

function handlePrevPoi() {
  emit('prev-poi');
}

function handleNextPoi() {
  emit('next-poi');
}

function handlePoiClick(index) {
  emit('poi-click', index);
}

function handleCancelRoute() {
  emit('cancel-route');
}

function getStopName(stop, index) {
  if (stop.is_start) return "Start Point";
  if (stop.is_end) return "End Point";
  return stop.name || `Stop ${index + 1}`;
}

function truncateText(text, maxLength) {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

function formatNumber(num) {
  if (!num) return "0";
  return num.toLocaleString();
}

// Get current stop for display
const currentStop = computed(() => {
  if (!props.confirmedRoute?.stops || props.currentPoiIndex < 0) return null;
  return props.confirmedRoute.stops[props.currentPoiIndex];
});
</script>

<style scoped>
.route-navigation-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

/* Current Stop Card */
.current-stop-card {
  background: rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 14px;
}

.stop-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stop-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.stop-name-large {
  font-weight: 700;
  font-size: 1.1rem;
  flex: 1;
}

.stop-number {
  padding: 4px 8px;
  background: rgba(106, 92, 255, 0.3);
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: bold;
}

.stop-kinds {
  font-size: 0.85rem;
  opacity: 0.8;
  color: #d9e6ff;
}

.stop-metrics {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 0.85rem;
}

.stop-metrics .rating {
  color: #ffa500;
}

.stop-metrics .score {
  opacity: 0.8;
}

.stop-description {
  font-size: 0.9rem;
  opacity: 0.9;
  line-height: 1.5;
  margin-top: 4px;
}

.stop-wiki-info {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: 2px;
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
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.poi-item:hover {
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.2);
}

.poi-item.current-poi {
  background: rgba(106, 92, 255, 0.2);
  border-color: rgba(106, 92, 255, 0.4);
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

.poi-item.current-poi .poi-number {
  background: rgba(106, 92, 255, 0.5);
}

.poi-item.start-stop {
  border-left: 3px solid #00c853;
}

.poi-item.end-stop {
  border-left: 3px solid #ff3db3;
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

.poi-metrics {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  font-size: 0.75rem;
}

.poi-metrics .rating {
  color: #ffa500;
}

.poi-metrics .score {
  opacity: 0.8;
}

.poi-metrics .distance {
  opacity: 0.7;
}

.poi-description {
  font-size: 0.8rem;
  opacity: 0.85;
  line-height: 1.4;
  margin-top: 2px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.poi-wiki-info {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 2px;
}

.current-indicator {
  font-size: 1.2rem;
  flex-shrink: 0;
}

/* Scrollbar */
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

.poi-list-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.3);
}
</style>


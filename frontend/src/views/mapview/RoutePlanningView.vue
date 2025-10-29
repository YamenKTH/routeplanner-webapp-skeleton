<template>
  <div>
    <h3 class="panel-title">Plan Your Route</h3>
    <h4 class="panel-title-small">Click anywhere on the map to choose your destination</h4>

    <!-- MAIN CONTROLS -->
    <div class="dense-grid">
      <!-- Time -->
      <div class="panel-section compact">
        <label class="label">Time</label>
        <div class="slider-row cardish compact">
          <span class="icon">🕒</span>
          <input 
            type="range" 
            :modelValue="timeMin" 
            @input="handleTimeChange" 
            min="10" 
            max="180" 
            step="5" 
            class="horizontal-slider slim" 
          />
          <span class="slider-value">{{ (timeMin / 60).toFixed(1) }} h</span>
        </div>
      </div>

      <!-- Trip mode -->
      <div class="row-two compact radio-group">
        <label class="chk-pill small">
          <input 
            type="radio" 
            name="tripMode" 
            value="round" 
            :checked="tripMode === 'round'"
            @change="handleTripModeChange('round')" 
          />
          <img src="/src/icons/roundTripIcon.jpg" alt="Round Trip" class="option-icon" />
          <span>Round Trip</span>
        </label>
        <label class="chk-pill small">
          <input 
            type="radio" 
            name="tripMode" 
            value="end" 
            :checked="tripMode === 'end'"
            @change="handleTripModeChange('end')" 
          />
          <img src="/src/icons/endPositionsIcon.png" alt="End Position" class="option-icon" />
          <span>End Position</span>
        </label>
      </div>

      <!-- Advanced toggle in mid state -->
      <button v-if="sheetState === 'mid'" class="adv-toggle" @click="handleExpandAdvanced">
        Advanced settings
      </button>
    </div>

    <!-- ADVANCED -->
    <transition name="fade">
      <div v-if="sheetState === 'expanded'" class="advanced-box">
        <h4>Advanced settings</h4>
        <!-- Radius -->
        <div class="panel-section compact">
          <label class="label">Radius</label>
          <div class="slider-row cardish compact">
            <span class="icon">📏</span>
            <input 
              type="range" 
              :modelValue="radius" 
              @input="handleRadiusChange" 
              min="200" 
              max="3000" 
              step="50" 
              class="horizontal-slider slim" 
            />
            <span class="slider-value">{{ radius }} m</span>
          </div>
        </div>
        <!-- Vertical action buttons -->
        <div class="column-actions">
          <button type="button" class="chk-pill small as-button full">Personalize</button>
          <button type="button" class="chk-pill small as-button full">Add must-see</button>
          <button type="button" class="chk-pill small as-button full">Speed</button>
        </div>
      </div>
    </transition>
    
    <!-- Generate -->
    <button 
      class="generate-btn" 
      @click="handleGenerateRoute" 
      :disabled="isGenerating || !canGenerate"
    >
      <span class="btn-icon" :class="{ spinning: isGenerating }">▶️</span>
      {{ isGenerating ? "Building..." : "Generate Route" }}
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  timeMin: {
    type: Number,
    required: true,
  },
  radius: {
    type: Number,
    required: true,
  },
  tripMode: {
    type: String,
    required: true,
  },
  isGenerating: {
    type: Boolean,
    default: false,
  },
  canGenerate: {
    type: Boolean,
    default: false,
  },
  sheetState: {
    type: String,
    required: true,
  },
});

const emit = defineEmits([
  'update:timeMin',
  'update:radius',
  'update:tripMode',
  'update:sheetState',
  'generate-route',
]);

function handleTimeChange(event) {
  emit('update:timeMin', Number(event.target.value));
}

function handleRadiusChange(event) {
  emit('update:radius', Number(event.target.value));
}

function handleTripModeChange(value) {
  emit('update:tripMode', value);
}

function handleExpandAdvanced() {
  emit('update:sheetState', 'expanded');
}

function handleGenerateRoute() {
  emit('generate-route');
}
</script>

<style scoped>
.panel-title {
  text-align: center;
  margin: 0 0 1px;
  font-weight: 444;
  font-size: 1rem;
}

.panel-title-small {
  text-align: center;
  margin: 0 0 1px;
  font-weight: 444;
  font-size: 0.8rem;
  color: 666;
  font-style: italic;
}

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

/* Dense layout */
.dense-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.panel-section.compact {
  margin: 10px;
}

.label {
  font-size: .8rem;
  color: #d9e6ff;
  font-weight: 700;
  margin-bottom: 2px;
}

/* Slider */
.cardish.compact {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 10px;
  padding: 8px 10px;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon {
  font-size: 1.05rem;
}

.horizontal-slider.slim {
  flex: 1;
  -webkit-appearance: none;
  height: 5px;
  border-radius: 4px;
  background: linear-gradient(90deg,#7f66ff 0%,#b06cff 100%);
  cursor: pointer;
}

.horizontal-slider.slim::-webkit-slider-thumb,
.horizontal-slider.slim::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #7f66ff;
  cursor: pointer;
}

.slider-value {
  min-width: 56px;
  text-align: right;
  font-weight: 800;
  font-size: 0.9rem;
}

/* Pills */
.row-two.compact {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.chk-pill.small {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
  background: linear-gradient(90deg,#eef 0%,#f6f0ff 100%);
  color: #4b3d8f;
  border-radius: 10px;
  padding: 8px 6px;
  font-weight: 700;
  font-size: 0.9rem;
  border: none;
}

.chk-pill.small input[type="radio"] {
  accent-color: #6a5cff;
  transform: scale(1.2);
}

.option-icon {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  object-fit: cover;
}

.as-button {
  cursor: pointer;
}

.as-button.full {
  width: 100%;
}

/* Generate button */
.generate-btn {
  width: 100%;
  background: linear-gradient(135deg,#6a5cff 0%,#ff3db3 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 12px 0;
  font-size: 1.02rem;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(0,0,0,0.35);
  transition: transform .1s ease, box-shadow .2s ease;
}

.generate-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(0,0,0,0.45);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-icon {
  font-size: 1.1rem;
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Advanced */
.adv-toggle {
  background: transparent;
  border: none;
  color: #d9e6ff;
  font-size: .9rem;
  text-decoration: underline;
  cursor: pointer;
  justify-self: start;
  margin-bottom: 6px;
}

.advanced-box {
  margin-top: 10px;
  margin-bottom: 10px;
}

.advanced-box h4 {
  margin: 0 0 6px 2px;
}

/* Vertical actions */
.column-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Fade transition */
.fade-enter-active, .fade-leave-active {
  transition: opacity .2s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>


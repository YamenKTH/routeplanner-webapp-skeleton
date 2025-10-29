// Single-source-of-truth for the user's scorer settings (no Pinia).
import { reactive, toRefs, watch } from 'vue'

const STORAGE_KEY = 'scorer:v1'

// Keep defaults in sync with your Python Scorer.DEFAULT_CAT_WEIGHTS
const DEFAULT_CAT_WEIGHTS = {
  gardens_and_parks: 2,
  natural: 1.25,
  view_points: 1.2,
  historic: 1.2,
  museums: 1.1,
  architecture: 1.05,
  cultural: 1.1,
  urban_environment: 1,
  theatres_and_entertainments: 0.2,
  industrial_facilities: 0.3,
  foods: 0.3,
}

const state = reactive({
  catWeights: { ...DEFAULT_CAT_WEIGHTS },
})

// Load once on module import
try {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw) {
    const parsed = JSON.parse(raw)
    if (parsed && parsed.cat_weights && typeof parsed.cat_weights === 'object') {
      // merge so new defaults appear, user overrides win
      state.catWeights = { ...DEFAULT_CAT_WEIGHTS, ...parsed.cat_weights }
    }
  }
} catch { /* ignore */ }

// Clamp helper to keep values sane (product can explode otherwise)
function clamp(x, min = 0.1, max = 3.0) {
  const n = Number(x)
  if (Number.isNaN(n)) return min
  return Math.min(max, Math.max(min, n))
}

function setWeight(key, val) {
  state.catWeights[key] = clamp(val)
}

function resetScorer() {
  state.catWeights = { ...DEFAULT_CAT_WEIGHTS }
  save()
}

function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ cat_weights: state.catWeights }))
  } catch { /* ignore */ }
}

// Auto-persist on change
watch(
  () => state.catWeights,
  save,
  { deep: true }
)

// Multi-tab sync (optional)
window.addEventListener('storage', (e) => {
  if (e.key === STORAGE_KEY && e.newValue) {
    try {
      const parsed = JSON.parse(e.newValue)
      if (parsed && parsed.cat_weights) {
        state.catWeights = { ...DEFAULT_CAT_WEIGHTS, ...parsed.cat_weights }
      }
    } catch {}
  }
})

export function useScorer() {
  // expose state + helpers
  return {
    ...toRefs(state),
    setWeight,
    resetScorer,
    DEFAULT_CAT_WEIGHTS, // if views need to iterate full list
  }
}
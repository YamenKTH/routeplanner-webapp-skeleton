<template>
  <div id="map-container">
    <div id="map"></div>

    <!-- Mode Toggle Button -->
    <div class="mode-toggle">
      <button class="mode-btn" @click="toggleMode">
        {{ isRoutePlanningMode ? '📍 View Route' : '🗺️ Plan New Route' }}
      </button>
    </div>

    <!-- Bottom sheet -->
    <div class="bottom-sheet" :style="sheetStyle">
      <!-- Drag handle -->
      <div class="sheet-handle-area" @pointerdown="onPointerDown">
        <div class="sheet-handle-lines">
          <span></span><span></span>
        </div>
      </div>

      <div class="sheet-content">
        <!-- ROUTE NAVIGATION VIEW (when route is confirmed) -->
        <div v-if="confirmedRoute && !isRoutePlanningMode" class="route-navigation-view">
          <div class="route-summary">
            <div class="route-stats">
              <span class="stat">📍 {{ confirmedRoute.stops.length }} stops</span>
              <span class="stat">📏 {{ confirmedRoute.distance }} km</span>
              <span class="stat">🕒 {{ confirmedRoute.time }}</span>
            </div>
          </div>
          
          <div class="current-poi-card">
            <h4>{{ currentPoiName }}</h4>
            <div class="poi-details">
              <div class="poi-info" v-if="currentPoiDetails">
                <div class="poi-categories">{{ currentPoiDetails.categories }}</div>
                <div class="poi-description">{{ currentPoiDetails.description }}</div>
              </div>
            </div>
            <div class="poi-navigation">
              <button class="nav-btn" @click="prevPoi" :disabled="currentPoiIndex === 0">⬅️ Previous</button>
              <span class="poi-counter">{{ currentPoiIndex + 1 }} / {{ confirmedRoute.stops.length }}</span>
              <button class="nav-btn" @click="nextPoi" :disabled="currentPoiIndex === confirmedRoute.stops.length - 1">Next ➡️</button>
            </div>
          </div>
        </div>

        <!-- ROUTE SELECTION VIEW (after generating routes, before confirmation) -->
        <div v-else-if="selectedEndStart && isRoutePlanningMode" class="route-selection-view">
          <h3 class="panel-title">Select Your Route</h3>
          
          <!-- Route navigation -->
          <div class="route-selection">
            <div class="route-nav">
              <button class="route-nav-btn" @click="prevRoute" :disabled="currentRouteIndex === 0 || isSwitchingRoute">
                <span v-if="isSwitchingRoute" class="btn-icon spinning">🔄</span>
                <span v-else>⬅️</span>
              </button>
              <span class="route-counter">Route {{ currentRouteIndex + 1 }} / {{ generatedRoutes.length }}</span>
              <button class="route-nav-btn" @click="nextRoute" :disabled="currentRouteIndex === generatedRoutes.length - 1 || isSwitchingRoute">
                <span v-if="isSwitchingRoute" class="btn-icon spinning">🔄</span>
                <span v-else>➡️</span>
              </button>
            </div>
            <button class="confirm-route-btn" @click="confirmRoute">Confirm This Route</button>
          </div>

          <!-- Route information -->
          <div class="route-info-card">
            <div class="route-stats-large">
              <div class="stat-item">
                <span class="stat-icon">📍</span>
                <div class="stat-content">
                  <div class="stat-value">{{ currentRoute.stops.length }} stops</div>
                  <div class="stat-label">Points of Interest</div>
                </div>
              </div>
              <div class="stat-item">
                <span class="stat-icon">📏</span>
                <div class="stat-content">
                  <div class="stat-value">{{ currentRoute.distance }} km</div>
                  <div class="stat-label">Total Distance</div>
                </div>
              </div>
              <div class="stat-item">
                <span class="stat-icon">🕒</span>
                <div class="stat-content">
                  <div class="stat-value">{{ currentRoute.time }}</div>
                  <div class="stat-label">Estimated Time</div>
                </div>
              </div>
            </div>
          </div>

          <!-- POI List -->
          <div class="poi-list-container">
            <h4 class="poi-list-title">Points of Interest</h4>
            <div class="poi-list">
              <div v-for="(stop, index) in currentRoute.stops" :key="index" 
                   class="poi-list-item" :class="{ 'current-poi': index === 0 }">
                <div class="poi-number">{{ index + 1 }}</div>
                <div class="poi-content">
                  <div class="poi-name">{{ stop.name || `Stop ${index + 1}` }}</div>
                  <div class="poi-categories" v-if="stop.categories">{{ stop.categories.join(', ') }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- INITIAL PLANNING VIEW (before generating routes) -->
        <div v-else-if="isRoutePlanningMode && !selectedEndStart">
          <h3 class="panel-title">Plan Your Route</h3>

          <!-- MAIN CONTROLS -->
          <div class="dense-grid">
            <!-- Time -->
            <div class="panel-section compact">
              <label class="label">Time</label>
              <div class="slider-row cardish compact">
                <span class="icon">🕒</span>
                <input type="range" v-model.number="timeMin" min="10" max="180" step="5" class="horizontal-slider slim" />
                <span class="slider-value">{{ (timeMin / 60).toFixed(1) }} h</span>
              </div>
            </div>

            <!-- Trip mode -->
            <div class="row-two compact radio-group">
              <label class="chk-pill small">
                <input type="radio" name="tripMode" value="round" v-model="tripMode" />
                <img src="/src/icons/roundTripIcon.jpg" alt="Round Trip" class="option-icon" />
                <span>Round Trip</span>
              </label>
              <label class="chk-pill small">
                <input type="radio" name="tripMode" value="end" v-model="tripMode" />
                <img src="/src/icons/endPositionsIcon.png" alt="End Position" class="option-icon" />
                <span>End Position</span>
              </label>
            </div>

            <!-- Advanced toggle in mid state -->
            <button v-if="sheetState==='mid'" class="adv-toggle" @click="sheetState='expanded'">
              Advanced settings
            </button>
          </div>

          <!-- ADVANCED -->
          <transition name="fade">
            <div v-if="sheetState==='expanded'" class="advanced-box">
              <h4>Advanced settings</h4>
              <!-- Radius -->
              <div class="panel-section compact">
                <label class="label">Radius</label>
                <div class="slider-row cardish compact">
                  <span class="icon">📏</span>
                  <input type="range" v-model.number="radius" min="200" max="3000" step="50" class="horizontal-slider slim" />
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
          <button class="generate-btn" @click="generateRoute" :disabled="isGenerating || !canGenerate">
            <span class="btn-icon" :class="{ spinning: isGenerating }">▶️</span>
            {{ isGenerating ? "Building..." : "Generate Route" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from "vue";
import axios from "axios";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { useScorer } from "../composables/useScorer.js";

const { catWeights } = useScorer();
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "/api" });

/* ---------------- state ---------------- */
const timeMin = ref(60);
const radius = ref(700);
const lat = ref(59.3293);
const lon = ref(18.0686);
const tripMode = ref("round");
const isGenerating = ref(false);
const isSwitchingRoute = ref(false);

// Route management
const generatedRoutes = ref([]);
const currentRouteIndex = ref(0);
const confirmedRoute = ref(null);
const currentPoiIndex = ref(0);
const isRoutePlanningMode = ref(true);
const selectedEndStart = ref(false); // New state to track if we're selecting between routes

// End position management
const endPositionSelected = ref(false);
const endLat = ref(null);
const endLon = ref(null);

let map, origin, circle, poiCluster, tourLayer;
let endMarker = null;
const candidateEnd = ref(null);
let tempEndMarker = null;
window._stopMarkers = [];

// Track route POIs to avoid duplicates
let routePoiMarkers = [];

/* ---------------- computed properties ---------------- */
const canGenerate = computed(() => {
  if (tripMode.value === "round") return true;
  return endPositionSelected.value && !!endLat.value && !!endLon.value;
});

const currentRoute = computed(() => {
  return generatedRoutes.value[currentRouteIndex.value] || {};
});

const currentPoiName = computed(() => {
  if (!confirmedRoute.value || !confirmedRoute.value.stops || confirmedRoute.value.stops.length === 0) return "";
  const stop = confirmedRoute.value.stops[currentPoiIndex.value];
  return stop.name || `Stop ${currentPoiIndex.value + 1}`;
});

const currentPoiDetails = computed(() => {
  if (!confirmedRoute.value || !confirmedRoute.value.stops || confirmedRoute.value.stops.length === 0) return null;
  const stop = confirmedRoute.value.stops[currentPoiIndex.value];
  return {
    categories: stop.categories ? stop.categories.join(', ') : 'No categories',
    description: stop.description || 'No description available'
  };
});

/* ---------------- bottom sheet ---------------- */
const STATES = ["peek", "mid", "expanded"];
const STATE_POS = { peek: 88, mid: 1, expanded: 0 };
const sheetState = ref("mid");
const STEP_TRIGGER_PX = 28;

const dragging = ref(false);
let dragStartY = 0, lastY = 0, dragStartTranslate = STATE_POS[sheetState.value], dragTranslate = STATE_POS[sheetState.value];

const sheetStyle = computed(() => ({
  transform: `translateY(${dragging.value ? dragTranslate : STATE_POS[sheetState.value]}%)`,
}));

function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
function getY(evt) {
  if (evt.touches && evt.touches.length) return evt.touches[0].clientY;
  if (evt.changedTouches && evt.changedTouches.length) return evt.changedTouches[0].clientY;
  return -evt.clientY;
}
function onPointerDown(e) {
  dragging.value = true;
  dragStartY = getY(e);
  lastY = dragStartY;
  dragStartTranslate = STATE_POS[sheetState.value];
  dragTranslate = dragStartTranslate;
  window.addEventListener("pointermove", onPointerMove, { passive: true });
  window.addEventListener("pointerup", onPointerUp, { passive: true });
  window.addEventListener("touchmove", onPointerMove, { passive: true });
  window.addEventListener("touchend", onPointerUp, { passive: true });
}
function onPointerMove(e) {
  if (!dragging.value) return;
  const y = getY(e);
  const dy = y - dragStartY;
  const vh = window.innerHeight || 1;
  const dyPct = (dy / vh) * 100;
  dragTranslate = clamp(dragStartTranslate + dyPct, 0, 92);
  lastY = y;
}
function snapStepwiseByPixels(currentState, startY, endY) {
  const dyPx = startY - endY;
  const idx = STATES.indexOf(currentState);
  if (dyPx >= STEP_TRIGGER_PX) return idx > 0 ? STATES[idx - 1] : currentState;
  if (dyPx <= -STEP_TRIGGER_PX) return idx < STATES.length - 1 ? STATES[idx + 1] : currentState;
  return currentState;
}
function onPointerUp() {
  if (!dragging.value) return;
  dragging.value = false;
  const target = snapStepwiseByPixels(sheetState.value, dragStartY, lastY);
  sheetState.value = target;
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  window.removeEventListener("touchmove", onPointerMove);
  window.removeEventListener("touchend", onPointerUp);
}

/* ---------------- Mode Toggle ---------------- */
function toggleMode() {
  isRoutePlanningMode.value = !isRoutePlanningMode.value;
  if (isRoutePlanningMode.value && confirmedRoute.value) {
    // When switching back to planning mode, keep the route displayed but allow modifications
    displayRoute(confirmedRoute.value);
    selectedEndStart.value = false;
  } else if (confirmedRoute.value) {
    // When switching to navigation mode, focus on current POI
    zoomToCurrentPoi();
  }
}

/* ---------------- feedback helper ---------------- */
function toast(msg) {
  const el = document.createElement("div");
  el.textContent = msg;
  Object.assign(el.style, {
    position: "fixed",
    bottom: "90px",
    left: "50%",
    transform: "translateX(-50%)",
    background: "rgba(15,22,32,0.9)",
    color: "#eef4ff",
    padding: "8px 14px",
    borderRadius: "8px",
    fontSize: ".85rem",
    zIndex: "9999",
    transition: "opacity 0.3s",
  });
  document.body.appendChild(el);
  setTimeout(() => (el.style.opacity = "0"), 1000);
  setTimeout(() => el.remove(), 1300);
}

/* ---------------- marker icons ---------------- */
const startIcon = L.icon({
  iconUrl: new URL("/src/icons/StartMarker.png", import.meta.url).href,
  iconSize: [40, 40],
});

const midIcon = L.icon({
  iconUrl: new URL("/src/icons/RoutePOIMarker.png", import.meta.url).href,
  iconSize: [20, 20],
});

const currentPoiIcon = L.icon({
  iconUrl: new URL("/src/icons/RoutePOIMarker.png", import.meta.url).href,
  iconSize: [30, 30], // Larger size for current POI
});

const endIcon = L.icon({
  iconUrl: new URL("/src/icons/endPositionsIcon.png", import.meta.url).href,
  iconSize: [35, 35],
});

const poiGreenIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [22, 34],
  iconAnchor: [11, 34],
  shadowSize: [41, 41],
});

const poiGrayIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [22, 34],
  iconAnchor: [11, 34],
  shadowSize: [41, 41],
});

const routePoiIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  shadowSize: [41, 41],
});

/* ---------------- popup builder ---------------- */
function buildPoiPopup(props, isCoordinatePopup = false) {
  try {
    // Don't show set as start/end buttons when in route selection mode
    if (selectedEndStart.value) {
      if (isCoordinatePopup) {
        // Simple coordinate display without buttons
        return `
          <div style="min-width: 180px; padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 8px; font-size: 14px;">📍 Coordinates</div>
            <div style="background: #f8f9fa; padding: 6px; border-radius: 4px; font-family: monospace; font-size: 12px; border: 1px solid #e9ecef;">
              ${props.lat.toFixed(5)}, ${props.lon.toFixed(5)}
            </div>
          </div>
        `;
      }

      // Regular POI popup without set as start/end buttons
      const name = props?.name || "Unnamed";
      const kinds = (props?.kinds || []).slice(0, 4).join(", ");
      const rawRate = props?.raw_rate ?? "";
      const d = props?.distance_m ?? props?.d ?? "";
      const det = props?.det || {};
      const wv = props?.wv || props?.wiki || null;

      let wikiExtract = det?.wikipedia_extracts?.text || "";
      if (wikiExtract && wikiExtract.length > 120) wikiExtract = wikiExtract.slice(0, 120) + "…";

      const xid = props?.xid;
      const otm = det?.otm || det?.url || (xid ? `https://opentripmap.com/en/card?xid=${encodeURIComponent(xid)}` : "#");

      let wikiLine = "";
      if (wv?.project && wv?.title) {
        const wpUrl = `https://${wv.project}/wiki/${wv.title}`;
        const views = (wv.views_365 ?? 0).toLocaleString();
        wikiLine = `📖 ${views} views • <a target="_blank" href="${wpUrl}" style="color: #6a5cff; text-decoration: none;">Open article</a>`;
      }

      return `
        <div style="min-width: 220px; max-width: 260px; padding: 10px;">
          <div style="font-weight: bold; margin-bottom: 6px; font-size: 14px;">${name}</div>
          <div style="font-size: 12px; color: #666; margin-bottom: 6px;">
            ${rawRate ? `⭐ ${rawRate} • ` : ''}${d ? `${d}m • ` : ''}<span style="font-size: 11px;">${kinds}</span>
          </div>
          ${wikiExtract ? `<div style="font-size: 12px; margin: 8px 0; line-height: 1.3;">${wikiExtract}</div>` : ''}
          ${wikiLine ? `<div style="font-size: 11px; margin-bottom: 8px;">${wikiLine}</div>` : ''}
          <div style="margin-bottom: 8px;">
            <a target="_blank" href="${otm}" style="font-size: 12px; color: #6a5cff; text-decoration: none;">📌 OpenTripMap</a>
          </div>
        </div>
      `;
    }

    // Original popup with set as start/end buttons (when not in route selection mode)
    if (isCoordinatePopup) {
      return `
        <div style="min-width: 180px; padding: 8px;">
          <div style="font-weight: bold; margin-bottom: 8px; font-size: 14px;">📍 Coordinates</div>
          <div style="background: #f8f9fa; padding: 6px; border-radius: 4px; margin-bottom: 10px; font-family: monospace; font-size: 12px; border: 1px solid #e9ecef;">
            ${props.lat.toFixed(5)}, ${props.lon.toFixed(5)}
          </div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            <button onclick="window.setAsStartFromPopup(${props.lat}, ${props.lon})" 
                    style="padding: 6px 10px; background: #6a5cff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
              Set as Start
            </button>
            <button onclick="window.setAsEndFromPopup(${props.lat}, ${props.lon})" 
                    style="padding: 6px 10px; background: #ff3db3; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;">
              Set as End
            </button>
          </div>
        </div>
      `;
    }

    // Regular POI popup with set as start/end buttons
    const name = props?.name || "Unnamed";
    const kinds = (props?.kinds || []).slice(0, 4).join(", ");
    const rawRate = props?.raw_rate ?? "";
    const d = props?.distance_m ?? props?.d ?? "";
    const det = props?.det || {};
    const wv = props?.wv || props?.wiki || null;

    let wikiExtract = det?.wikipedia_extracts?.text || "";
    if (wikiExtract && wikiExtract.length > 120) wikiExtract = wikiExtract.slice(0, 120) + "…";

    const xid = props?.xid;
    const otm = det?.otm || det?.url || (xid ? `https://opentripmap.com/en/card?xid=${encodeURIComponent(xid)}` : "#");

    let wikiLine = "";
    if (wv?.project && wv?.title) {
      const wpUrl = `https://${wv.project}/wiki/${wv.title}`;
      const views = (wv.views_365 ?? 0).toLocaleString();
      wikiLine = `📖 ${views} views • <a target="_blank" href="${wpUrl}" style="color: #6a5cff; text-decoration: none;">Open article</a>`;
    }
    
    return `
      <div style="min-width: 220px; max-width: 260px; padding: 10px;">
        <div style="font-weight: bold; margin-bottom: 6px; font-size: 14px;">${name}</div>
        <div style="font-size: 12px; color: #666; margin-bottom: 6px;">
          ${rawRate ? `⭐ ${rawRate} • ` : ''}${d ? `${d}m • ` : ''}<span style="font-size: 11px;">${kinds}</span>
        </div>
        ${wikiExtract ? `<div style="font-size: 12px; margin: 8px 0; line-height: 1.3;">${wikiExtract}</div>` : ''}
        ${wikiLine ? `<div style="font-size: 11px; margin-bottom: 8px;">${wikiLine}</div>` : ''}
        <div style="margin-bottom: 8px;">
          <a target="_blank" href="${otm}" style="font-size: 12px; color: #6a5cff; text-decoration: none;">📌 OpenTripMap</a>
        </div>
        <div style="border-top: 1px solid #eee; padding-top: 8px; display: flex; gap: 6px;">
          <button onclick="window.setAsStartFromPopup(${props.lat || props.geometry?.coordinates[1]}, ${props.lon || props.geometry?.coordinates[0]})" 
                  style="flex: 1; padding: 6px 8px; background: #6a5cff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
            Start
          </button>
          <button onclick="window.setAsEndFromPopup(${props.lat || props.geometry?.coordinates[1]}, ${props.lon || props.geometry?.coordinates[0]})" 
                  style="flex: 1; padding: 6px 8px; background: #ff3db3; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">
            End
          </button>
        </div>
      </div>
    `;
    
  } catch {
    const name = props?.name || "Place";
    const kinds = (props?.kinds || []).slice(0, 4).join(", ");
    return `
      <div style="min-width: 180px; padding: 10px;">
        <div style="font-weight: bold; margin-bottom: 6px;">${name}</div>
        <div style="font-size: 12px; color: #666;">${kinds}</div>
      </div>
    `;
  }
}

// Expose functions to global scope for popup buttons
window.setAsStartFromPopup = (lat, lon) => {
  setAsStart(lat, lon);
};

window.setAsEndFromPopup = (lat, lon) => {
  setAsEnd(lat, lon);
};

function setAsStart(lat, lon) {
  // Update the start position
  origin.setLatLng([lat, lon]);
  circle.setLatLng([lat, lon]);
  
  // Show feedback
  toast("✅ Start position updated!");
  
  // Close any open popups
  map.closePopup();
  
  // Reload POIs around the new start position
  loadPois();
}

function setAsEnd(lat, lon) {
  if (tripMode.value !== "end") {
    tripMode.value = "end";
  }
  
  // Set end position
  endLat.value = lat;
  endLon.value = lon;
  endPositionSelected.value = true;
  
  // Update or create end marker
  if (endMarker) endMarker.remove();
  endMarker = L.marker([endLat.value, endLon.value], { icon: endIcon }).addTo(map);
  
  // Show feedback
  toast("✅ End position set! You can now generate your route.");
  
  // Close any open popups
  map.closePopup();
}

function clearEndPosition() {
  endPositionSelected.value = false;
  endLat.value = null;
  endLon.value = null;
  if (endMarker) {
    endMarker.remove();
    endMarker = null;
  }
  toast("🗺️ End position cleared. Click on the map to select a new one.");
}

/* ---------------- map click ---------------- */
function onMapClick(e) {
  const { lat: clat, lng: clng } = e.latlng;
  
  // Don't show coordinate popup when in route selection mode
  if (selectedEndStart.value) {
    return;
  }
  
  // Show compact coordinate popup for both modes when not in route selection
  const popupContent = buildPoiPopup({ lat: clat, lon: clng }, true);
  L.popup()
    .setLatLng(e.latlng)
    .setContent(popupContent)
    .openOn(map);
}

/* ---------------- API: Load POIs ---------------- */
async function loadPois() {
  const payload = {
    lat: lat.value,
    lon: lon.value,
    radius_m: radius.value,
    cat_weights: { ...catWeights.value },
  };

  const { data } = await api.post("/api/pois", payload);

  if (poiCluster) poiCluster.remove();
  poiCluster = L.markerClusterGroup({
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
  });

  (data.features || []).forEach((f) => {
    const [gLon, gLat] = f.geometry.coordinates;
    const props = f.properties || {};
    const popupHtml = buildPoiPopup({ ...props, lat: gLat, lon: gLon, geometry: f.geometry });
    const hasWiki = !!((props.wv || props.wiki)?.title);
    const icon = hasWiki ? poiGreenIcon : poiGrayIcon;
    
    const marker = L.marker([gLat, gLon], { icon }).bindPopup(popupHtml, {
      maxWidth: 280,
      className: "wiki-popup",
    });
    
    poiCluster.addLayer(marker);
  });

  map.addLayer(poiCluster);
}

/* ---------------- Route Management ---------------- */
async function prevRoute() {
  if (currentRouteIndex.value > 0 && !isSwitchingRoute.value) {
    isSwitchingRoute.value = true;
    
    // Simulate API call with loading
    setTimeout(async () => {
      currentRouteIndex.value--;
      // For now, just use the existing generated route data
      // Later, you can replace this with actual API call to get different route
      await buildTour(); // This will regenerate routes with current parameters
      isSwitchingRoute.value = false;
    }, 800);
  }
}

async function nextRoute() {
  if (currentRouteIndex.value < generatedRoutes.value.length - 1 && !isSwitchingRoute.value) {
    isSwitchingRoute.value = true;
    
    // Simulate API call with loading
    setTimeout(async () => {
      currentRouteIndex.value++;
      // For now, just use the existing generated route data
      // Later, you can replace this with actual API call to get different route
      await buildTour(); // This will regenerate routes with current parameters
      isSwitchingRoute.value = false;
    }, 800);
  }
}

function confirmRoute() {
  confirmedRoute.value = generatedRoutes.value[currentRouteIndex.value];
  currentPoiIndex.value = 0;
  isRoutePlanningMode.value = false;
  updateRoutePoiMarkers();
  zoomToCurrentPoi();
  sheetState.value = "mid";
}

function prevPoi() {
  if (currentPoiIndex.value > 0) {
    currentPoiIndex.value--;
    updateRoutePoiMarkers();
    zoomToCurrentPoi();
  }
}

function nextPoi() {
  if (confirmedRoute.value && currentPoiIndex.value < confirmedRoute.value.stops.length - 1) {
    currentPoiIndex.value++;
    updateRoutePoiMarkers();
    zoomToCurrentPoi();
  }
}

function zoomToCurrentPoi() {
  if (!confirmedRoute.value || !confirmedRoute.value.stops || confirmedRoute.value.stops.length === 0) return;
  
  const stop = confirmedRoute.value.stops[currentPoiIndex.value];
  map.setView([stop.lat, stop.lon], 17);
}

function updateRoutePoiMarkers() {
  // Clear existing route POI markers
  routePoiMarkers.forEach(marker => marker.remove());
  routePoiMarkers = [];

  if (!confirmedRoute.value || !confirmedRoute.value.stops) return;

  // Add route POIs with special styling
  confirmedRoute.value.stops.forEach((stop, index) => {
    let icon;
    if (index === 0) {
      icon = startIcon; // Start marker
    } else if (index === confirmedRoute.value.stops.length - 1 && tripMode.value === "end") {
      icon = endIcon; // End marker
    } else if (index === currentPoiIndex.value) {
      icon = currentPoiIcon; // Current POI - larger and highlighted
    } else {
      icon = routePoiIcon; // Other route POIs - blue color to distinguish from regular POIs
    }

    const marker = L.marker([stop.lat, stop.lon], { icon })
      .bindPopup(`<b>${stop.name || `Stop ${index + 1}`}</b><br/>Route point`);
    
    marker.addTo(map);
    routePoiMarkers.push(marker);
  });
}

/* ---------------- API: Build Tour ---------------- */
async function buildTour() {
  try {
    const isRound = tripMode.value === "round";
    const isEnd = tripMode.value === "end";
    const payload = {
      lat: Number(lat.value),
      lon: Number(lon.value),
      time_min: Number(timeMin.value),
      radius_m: Number(radius.value),
      roundtrip: isRound,
      end_lat: isEnd && endPositionSelected.value ? Number(endLat.value) : null,
      end_lon: isEnd && endPositionSelected.value ? Number(endLon.value) : null,
      router: "osrm",
      router_url: "http://osrm:5000",
      snap_path: true,
      cat_weights: { ...catWeights.value },
    };

    const { data } = await api.post("/api/tour", payload);
    
    // For now, create 5 hardcoded routes (in real implementation, these would come from backend)
    generatedRoutes.value = Array(5).fill(null).map((_, index) => ({
      ...data,
      id: index,
      distance: (Math.random() * 5 + 2).toFixed(1),
      time: `${Math.floor(Math.random() * 120 + 30)} min`,
      stops: (data.stops || []).map((stop, stopIndex) => ({
        ...stop,
        name: stop.name || `POI ${stopIndex + 1}`,
        categories: ['Landmark', 'Cultural', 'Historical'].slice(0, Math.floor(Math.random() * 3) + 1),
        description: 'This is a point of interest along your route with interesting features to explore.'
      }))
    }));
    
    currentRouteIndex.value = 0;
    confirmedRoute.value = null;
    isRoutePlanningMode.value = true;
    
    displayRoute(generatedRoutes.value[0]);
    sheetState.value = "mid";
    
  } catch (err) {
    console.error("Failed to build tour:", err);
  }
}

function displayRoute(routeData) {
  if (tourLayer) tourLayer.remove();
  window._stopMarkers.forEach((m) => m.remove());
  window._stopMarkers = [];
  routePoiMarkers.forEach(marker => marker.remove());
  routePoiMarkers = [];

  if (routeData?.path) {
    tourLayer = L.geoJSON(routeData.path, {
      style: { color: "#C42DE3", weight: 3.5, opacity: 1 },
    }).addTo(map);
  }

  // Use the special route POI markers instead of the default ones
  updateRoutePoiMarkers();

  if (tourLayer && tourLayer.getBounds().isValid()) {
    map.fitBounds(tourLayer.getBounds(), { padding: [20, 20] });
  }
}

/* ---------------- generate ---------------- */
async function generateRoute() {
  if (isGenerating.value) return;
  isGenerating.value = true;
  try {
    await buildTour();
    // Flip the state to show route selection view
    selectedEndStart.value = true;
  } finally {
    isGenerating.value = false;
  }
}

/* ---------------- map setup ---------------- */
onMounted(() => {
  const el = document.getElementById("map");
  if (el) el.style.height = "100%";

  map = L.map("map").setView([lat.value, lon.value], 14);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);

  origin = L.marker([lat.value, lon.value], {
    draggable: true,
    icon: startIcon,
  }).addTo(map);

  origin.on("dragend", async (e) => {
    const c = e.target.getLatLng();
    lat.value = c.lat;
    lon.value = c.lng;
    circle.setLatLng(c);
    if (tourLayer) {
      tourLayer.remove();
      tourLayer = null;
    }
    window._stopMarkers.forEach((m) => m.remove());
    window._stopMarkers = [];
    routePoiMarkers.forEach(marker => marker.remove());
    routePoiMarkers = [];
    await loadPois();
  });

  circle = L.circle([lat.value, lon.value], {
    radius: radius.value,
    fillOpacity: 0.15,
    color: "#1BB9F5",
    weight: 2.9,
  }).addTo(map);

  loadPois();
  map.on("click", onMapClick);
});

onBeforeUnmount(() => {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  window.removeEventListener("touchmove", onPointerMove);
  window.removeEventListener("touchend", onPointerUp);
});

watch(radius, (v) => {
  if (circle) {
    circle.setRadius(v);
    loadPois();
  }
});

watch(tripMode, (v) => {
  if (v === "end") {
    if (!endPositionSelected.value) {
      toast("🗺️ Click anywhere on the map to choose your destination");
    }
  } else {
    // When switching away from end mode, clear the end position
    clearEndPosition();
  }
});
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
}

#map-container {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

#map {
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* Mode Toggle */
.mode-toggle {
  position: absolute;
  top: 80px;
  right: 20px;
  z-index: 1000;
}

.mode-btn {
  background: linear-gradient(135deg, #6a5cff 0%, #ff3db3 100%);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 10px 16px;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  z-index: 1000;
}

/* Bottom sheet */
.bottom-sheet {
  position: absolute;
  right: 5%;
  bottom: 0;
  width: 90%;
  background: rgba(15, 22, 32, 0.48);
  color: #eef4ff;
  backdrop-filter: blur(2px) saturate(115%);
  -webkit-backdrop-filter: blur(2px) saturate(115%);
  border-radius: 14px 14px 0 0;
  box-shadow: 0 -10px 30px rgba(0,0,0,0.35);
  z-index: 1002;
  transition: transform 220ms ease;
  will-change: transform;
}

/* Drag handle */
.sheet-handle-area {
  width: 100%;
  height: 33px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  user-select: none;
  touch-action: pan-y;
}

.sheet-handle-lines {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.sheet-handle-lines span {
  display: block;
  width: 42px;
  height: 4px;
  border-radius: 4px;
  background: rgba(255,255,255,0.7);
}

/* Content */
.sheet-content {
  padding: 6px 14px 14px;
  overflow: hidden;
}

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

/* Position Display */
.position-display {
  margin-bottom: 8px;
}

.position-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.position-title {
  font-weight: bold;
  font-size: 0.9rem;
}

.current-coordinates {
  font-size: 0.8rem;
  opacity: 0.9;
  font-family: monospace;
}

/* End Position Controls */
.end-position-controls {
  margin-bottom: 8px;
}

.end-position-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.end-position-title {
  font-weight: bold;
  font-size: 0.9rem;
}

.end-position-options {
  text-align: center;
}

.option-description {
  font-size: 0.8rem;
  margin-bottom: 6px;
  opacity: 0.9;
}

.selection-hint {
  font-size: 0.75rem;
  color: #ffa500;
  font-style: italic;
}

.end-position-selected {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selected-coordinates {
  flex: 1;
}

.coord-display-small {
  font-size: 0.75rem;
  opacity: 0.9;
  margin-top: 2px;
  font-family: monospace;
}

.change-end-btn {
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  color: #eef4ff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  cursor: pointer;
}

/* Route Navigation View */
.route-navigation-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.route-summary {
  background: rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 12px;
}

.route-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
}

.current-poi-card {
  background: rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 12px;
}

.current-poi-card h4 {
  margin: 0 0 10px 0;
  text-align: center;
}

.poi-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.nav-btn {
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.3);
  color: #eef4ff;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.poi-counter {
  font-weight: bold;
  font-size: 0.9rem;
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

/* Popup styles */
.leaflet-popup-content {
  margin: 8px !important;
  line-height: 1.4;
}

.wiki-popup .leaflet-popup-content-wrapper {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Route Selection View */
.route-selection-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.route-info-card {
  background: rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 16px;
}

.route-stats-large {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.stat-icon {
  font-size: 1.5rem;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-weight: bold;
  font-size: 1.1rem;
}

.stat-label {
  font-size: 0.75rem;
  opacity: 0.8;
}

/* POI List */
.poi-list-container {
  background: rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.poi-list-title {
  margin: 0 0 12px 0;
  font-size: 1rem;
  font-weight: 600;
}

.poi-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.poi-list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.poi-list-item.current-poi {
  background: rgba(106, 92, 255, 0.15);
  border-color: rgba(106, 92, 255, 0.5);
}

.poi-number {
  width: 24px;
  height: 24px;
  background: rgba(106, 92, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: bold;
}

.poi-list-item.current-poi .poi-number {
  background: rgba(106, 92, 255, 0.8);
  color: white;
}

.poi-content {
  flex: 1;
}

.poi-name {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 2px;
}

.poi-categories {
  font-size: 0.75rem;
  opacity: 0.7;
}

/* Enhanced POI details in navigation view */
.poi-details {
  margin: 10px 0;
  padding: 10px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
}

.poi-info {
  font-size: 0.85rem;
}

.poi-categories {
  font-weight: 600;
  margin-bottom: 4px;
  color: #6a5cff;
}

.poi-description {
  opacity: 0.8;
  line-height: 1.3;
}

/* Route selection buttons with loading states */
.route-nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Scrollbar styling for POI list */
.poi-list-container::-webkit-scrollbar {
  width: 6px;
}

.poi-list-container::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.1);
  border-radius: 3px;
}

.poi-list-container::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.3);
  border-radius: 3px;
}

.poi-list-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.5);
}
</style>
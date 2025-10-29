<template>
  <div id="map-container">
    <div id="map"></div>

    <!-- Route Info Header (top of MapView container) -->
    <RouteInfoHeader
      v-if="confirmedRoute && !isRoutePlanningMode"
      :direction="nextStopDirection"
      :place="nextStopPlace"
      :distance="nextStopDistance"
    />

    <!-- Mode Toggle Button (only shown in planning mode before routes are generated) -->
    <div v-if="isRoutePlanningMode && generatedRoutes.length === 0" class="mode-toggle">
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
        <RouteNavigationView
          v-if="confirmedRoute && !isRoutePlanningMode"
          :confirmed-route="confirmedRoute"
          :current-poi-index="currentPoiIndex"
          @prev-poi="prevPoi"
          @next-poi="nextPoi"
          @poi-click="goToPoi"
          @cancel-route="cancelRoute"
        />

        <!-- PLANNING VIEW (settings before generate) -->
        <RoutePlanningView
          v-else-if="isRoutePlanningMode && generatedRoutes.length === 0"
          :time-min="timeMin"
          :radius="radius"
          :trip-mode="tripMode"
          :is-generating="isGenerating"
          :can-generate="canGenerate"
          :sheet-state="sheetState"
          @update:timeMin="timeMin = $event"
          @update:radius="radius = $event"
          @update:tripMode="tripMode = $event"
          @update:sheetState="sheetState = $event"
          @generate-route="generateRoute"
        />

        <!-- ROUTE SELECTION VIEW (after generate, before confirm) -->
        <RouteSelectionView
          v-else-if="isRoutePlanningMode && generatedRoutes.length > 0"
          :generated-routes="generatedRoutes"
          :current-route-index="currentRouteIndex"
          @prev-route="prevRoute"
          @next-route="nextRoute"
          @confirm-route="confirmRoute"
          @cancel-route="cancelRoute"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { useScorer } from "../../composables/useScorer.js";
import { loadPois as loadPoisApi, buildTour as buildTourApi } from "../../api/mapApi.js";
import RouteNavigationView from "./RouteNavigationView.vue";
import RoutePlanningView from "./RoutePlanningView.vue";
import RouteSelectionView from "./RouteSelectionView.vue";
import RouteInfoHeader from "../../components/RouteInfoHeader.vue";

const { catWeights } = useScorer();

/* ---------------- state ---------------- */
const timeMin = ref(60);
const radius = ref(700);
const lat = ref(59.3293);
const lon = ref(18.0686);
const tripMode = ref("round");
const isGenerating = ref(false);

// Route management
const generatedRoutes = ref([]);
const currentRouteIndex = ref(0);
const confirmedRoute = ref(null);
const currentPoiIndex = ref(0);
const isRoutePlanningMode = ref(true);

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

/* ---------------- bottom sheet ---------------- */
const STATES = ["peek", "mid", "expanded"];
const STATE_POS = { peek: 88, mid: 1, expanded: 0 };
const sheetState = ref("mid");
const STEP_TRIGGER_PX = 28;

const dragging = ref(false);
let dragStartY = 0, lastY = 0, dragStartTranslate = STATE_POS[sheetState.value], dragTranslate = STATE_POS[sheetState.value];

const canGenerate = computed(() => {
  if (tripMode.value === "round") return true;
  return endPositionSelected.value && !!endLat.value && !!endLon.value;
});

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
    if (isCoordinatePopup) {
      // Compact popup for random coordinate clicks
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

    // Regular POI popup - made more compact
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
  lat = lat;
  lon = lon;
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
  // Disable map click popups when in route selection or navigation mode
  if (isRoutePlanningMode.value && generatedRoutes.value.length > 0) {
    return; // Route selection view - no popups
  }
  if (confirmedRoute.value && !isRoutePlanningMode.value) {
    return; // Route navigation view - no popups
  }
  
  const { lat: clat, lng: clng } = e.latlng;
  
  // Show compact coordinate popup for planning mode only
  const popupContent = buildPoiPopup({ lat: clat, lon: clng }, true);
  L.popup()
    .setLatLng(e.latlng)
    .setContent(popupContent)
    .openOn(map);
}

/* ---------------- API: Load POIs ---------------- */
async function loadPois() {
  const data = await loadPoisApi(lat.value, lon.value, radius.value, catWeights.value);

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
function prevRoute() {
  if (currentRouteIndex.value > 0) {
    currentRouteIndex.value--;
    displayRoute(generatedRoutes.value[currentRouteIndex.value]);
  }
}

function nextRoute() {
  if (currentRouteIndex.value < generatedRoutes.value.length - 1) {
    currentRouteIndex.value++;
    displayRoute(generatedRoutes.value[currentRouteIndex.value]);
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

function goToPoi(index) {
  if (!confirmedRoute.value || !confirmedRoute.value.stops || index < 0 || index >= confirmedRoute.value.stops.length) return;
  currentPoiIndex.value = index;
  updateRoutePoiMarkers();
  zoomToCurrentPoi();
}

function editRoute() {
  // Switch back to planning mode to edit the route
  isRoutePlanningMode.value = true;
  sheetState.value = "mid";
}

function cancelRoute() {
  // Clear all route data and return to planning mode
  confirmedRoute.value = null;
  generatedRoutes.value = [];
  currentRouteIndex.value = 0;
  currentPoiIndex.value = 0;
  isRoutePlanningMode.value = true;
  
  // Remove route visualization
  if (tourLayer) {
    tourLayer.remove();
    tourLayer = null;
  }
  routePoiMarkers.forEach(marker => marker.remove());
  routePoiMarkers = [];
  
  sheetState.value = "mid";
}

// Navigation info for header (computed from RouteNavigationView logic)
const currentStop = computed(() => {
  if (!confirmedRoute.value?.stops || currentPoiIndex.value < 0) return null;
  return confirmedRoute.value.stops[currentPoiIndex.value];
});

const nextStop = computed(() => {
  if (!confirmedRoute.value?.stops || currentPoiIndex.value >= confirmedRoute.value.stops.length - 1) return null;
  return confirmedRoute.value.stops[currentPoiIndex.value + 1];
});

function getStopName(stop, index) {
  if (!stop) return "";
  if (stop.is_start) return "Start Point";
  if (stop.is_end) return "End Point";
  return stop.name || `Stop ${index + 1}`;
}

const nextStopDirection = computed(() => {
  if (!nextStop.value) return "🏁";
  // TODO: Get actual direction from route data
  return "➡️";
});

const nextStopPlace = computed(() => {
  if (!nextStop.value) return "Destination reached";
  return getStopName(nextStop.value, currentPoiIndex.value + 1);
});

function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371e3; // Earth radius in meters
  const φ1 = lat1 * Math.PI/180;
  const φ2 = lat2 * Math.PI/180;
  const Δφ = (lat2-lat1) * Math.PI/180;
  const Δλ = (lon2-lon1) * Math.PI/180;

  const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ/2) * Math.sin(Δλ/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

  return R * c;
}

const nextStopDistance = computed(() => {
  if (!nextStop.value || !currentStop.value) return null;
  // Calculate distance between current and next stop
  const dist = calculateDistance(
    currentStop.value.lat,
    currentStop.value.lon,
    nextStop.value.lat,
    nextStop.value.lon
  );
  if (dist < 1000) {
    return `${Math.round(dist)} m`;
  }
  return `${(dist / 1000).toFixed(1)} km`;
});

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
    if (stop.is_start || index === 0) {
      icon = startIcon; // Start marker
    } else if (stop.is_end || (index === confirmedRoute.value.stops.length - 1 && tripMode.value === "end")) {
      icon = endIcon; // End marker
    } else if (index === currentPoiIndex.value) {
      icon = currentPoiIcon; // Current POI - larger and highlighted
    } else {
      icon = routePoiIcon; // Other route POIs - blue color to distinguish from regular POIs
    }

    // Build detailed popup for POI stops
    let popupContent = "";
    if (stop.is_start) {
      popupContent = `<b>🚩 Start Point</b><br/>${stop.lat.toFixed(5)}, ${stop.lon.toFixed(5)}`;
    } else if (stop.is_end) {
      popupContent = `<b>🏁 End Point</b><br/>${stop.lat.toFixed(5)}, ${stop.lon.toFixed(5)}`;
    } else {
      // Use the same popup builder as regular POIs but with stop data
      popupContent = buildPoiPopup({
        name: stop.name,
        xid: stop.xid,
        lat: stop.lat,
        lon: stop.lon,
        kinds: stop.kinds || [],
        raw_rate: stop.raw_rate,
        score: stop.score,
        det: stop.det,
        wv: stop.wv,
        distance_m: stop.distance_m
      });
    }

    const marker = L.marker([stop.lat, stop.lon], { icon })
      .bindPopup(popupContent, { maxWidth: 280, className: "wiki-popup" });
    
    marker.addTo(map);
    routePoiMarkers.push(marker);
  });
}

/* ---------------- API: Build Tour ---------------- */
async function buildTour() {
  try {
    const isRound = tripMode.value === "round";
    const isEnd = tripMode.value === "end";
    
    const data = await buildTourApi({
      lat: lat.value,
      lon: lon.value,
      time_min: timeMin.value,
      radius_m: radius.value,
      roundtrip: isRound,
      end_lat: isEnd && endPositionSelected.value ? endLat.value : null,
      end_lon: isEnd && endPositionSelected.value ? endLon.value : null,
      router: "osrm",
      router_url: "http://osrm:5000",
      snap_path: true,
      cat_weights: catWeights.value,
    });
    
    // Backend now returns multiple routes in data.routes array
    // Support both old format (single route) and new format (multiple routes)
    if (data.routes && Array.isArray(data.routes)) {
      generatedRoutes.value = data.routes;
    } else {
      // Fallback for old API format (single route)
      generatedRoutes.value = [{
        ...data,
        id: "default",
        name: "default",
        distance: data.distance || "N/A",
        time: data.time || "N/A",
        stops: data.stops || []
      }];
    }
    
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

  // Add markers for the route being displayed (during route selection)
  if (routeData?.stops && routeData.stops.length > 0) {
    routeData.stops.forEach((stop, index) => {
      let icon;
      if (stop.is_start || index === 0) {
        icon = startIcon;
      } else if (stop.is_end || index === routeData.stops.length - 1) {
        icon = endIcon;
      } else {
        icon = routePoiIcon;
      }

      let popupContent = "";
      if (stop.is_start) {
        popupContent = `<b>🚩 Start Point</b><br/>${stop.lat.toFixed(5)}, ${stop.lon.toFixed(5)}`;
      } else if (stop.is_end) {
        popupContent = `<b>🏁 End Point</b><br/>${stop.lat.toFixed(5)}, ${stop.lon.toFixed(5)}`;
      } else {
        popupContent = buildPoiPopup({
          name: stop.name,
          xid: stop.xid,
          lat: stop.lat,
          lon: stop.lon,
          kinds: stop.kinds || [],
          raw_rate: stop.raw_rate,
          score: stop.score,
          det: stop.det,
          wv: stop.wv,
          distance_m: stop.distance_m
        });
      }

      const marker = L.marker([stop.lat, stop.lon], { icon })
        .bindPopup(popupContent, { maxWidth: 280, className: "wiki-popup" });
      
      marker.addTo(map);
      routePoiMarkers.push(marker);
    });
  }

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
  z-index: 1003;
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


/* Popup styles */
.leaflet-popup-content {
  margin: 8px !important;
  line-height: 1.4;
}

.wiki-popup .leaflet-popup-content-wrapper {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
</style>
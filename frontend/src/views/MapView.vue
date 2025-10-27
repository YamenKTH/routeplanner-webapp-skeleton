<template>
  <div id="map-container">
    <div id="map"></div>

    <!-- Bottom sheet -->
    <div class="bottom-sheet" :style="sheetStyle">
      <!-- Drag handle -->
      <div class="sheet-handle-area" @pointerdown="onPointerDown">
        <div class="sheet-handle-lines">
          <span></span><span></span>
        </div>
      </div>

      <div class="sheet-content">
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

          <!-- Generate -->
          <button class="generate-btn" @click="generateRoute" :disabled="isGenerating">
            <span class="btn-icon" :class="{ spinning: isGenerating }">▶️</span>
            {{ isGenerating ? "Building..." : "Generate Route" }}
          </button>

          <!-- Advanced toggle in mid state -->
          <button v-if="sheetState==='mid'" class="adv-toggle" @click="sheetState='expanded'">
            Advanced settings
          </button>
        </div>

        <!-- ADVANCED -->
        <transition name="fade">
          <div v-if="sheetState==='expanded'" class="advanced-box">
            <h4>Advanced settings</h4>

            <!-- Radius (moved here) -->
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
              <button type="button" class="chk-pill small as-button full">Speed</button>
              <button type="button" class="chk-pill small as-button full">Add must-see</button>
              <button type="button" class="chk-pill small as-button full">Personalize</button>
            </div>
          </div>
        </transition>
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

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "/api" });

/* ---------------- state ---------------- */
const timeMin = ref(60);
const radius = ref(700);
const lat = ref(59.3293);
const lon = ref(18.0686);
const tripMode = ref("round");
const isGenerating = ref(false);

let map, origin, circle, poiCluster, tourLayer;
let endMarker = null;
let endLat = null;
let endLon = null;
window._stopMarkers = [];

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

/* ---------------- marker icons ---------------- */
const startIcon = L.icon({
  iconUrl: new URL("/src/icons/StartMarker.png", import.meta.url).href,
  iconSize: [40, 40],
});

const midIcon = L.icon({
  iconUrl: new URL("/src/icons/RoutePOIMarker.png", import.meta.url).href,
  iconSize: [20, 20],
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

/* ---------------- popup builder ---------------- */
function buildPoiPopup(props) {
  try {
    const name = props?.name || "Unnamed";
    const kinds = (props?.kinds || []).slice(0, 6).join(", ");
    const rawRate = props?.raw_rate ?? "";
    const d = props?.distance_m ?? props?.d ?? "";
    const det = props?.det || {};
    const wv = props?.wv || props?.wiki || null;

    let wikiExtract = det?.wikipedia_extracts?.text || "";
    if (wikiExtract && wikiExtract.length > 280) wikiExtract = wikiExtract.slice(0, 280) + "…";

    const xid = props?.xid;
    const otm = det?.otm || det?.url || (xid ? `https://opentripmap.com/en/card?xid=${encodeURIComponent(xid)}` : "#");

    let wikiLine = "";
    if (wv?.project && wv?.title) {
      const wpUrl = `https://${wv.project}/wiki/${wv.title}`;
      const views = (wv.views_365 ?? 0).toLocaleString();
      const score = (wv.score ?? props?.score ?? 0);
      wikiLine = `📖 Wikipedia views (365d): <b>${views}</b> | Score: <b>${Math.round(score)}</b> • <a target="_blank" href="${wpUrl}">Open article</a>`;
    }

    return `
      <b>${name}</b><br/>
      OTM rate: ${rawRate} • Distance: ${d ? `${d} m` : ""}<br/>
      <small>${kinds}</small>
      <div style="margin-top:6px">${wikiExtract || ""}</div>
      <div style="margin-top:6px">${wikiLine}</div>
      <div style="margin-top:6px"><a target="_blank" href="${otm}">Open in OpenTripMap</a></div>
    `;
  } catch {
    const name = props?.name || "Place";
    const kinds = (props?.kinds || []).slice(0, 6).join(", ");
    return `<b>${name}</b><br/><small>${kinds}</small>`;
  }
}

/* ---------------- API: Load POIs ---------------- */
async function loadPois() {
  const payload = { lat: lat.value, lon: lon.value, radius_m: radius.value, cat_weights: {} };
  const { data } = await api.post("/api/pois", payload);

  if (poiCluster) poiCluster.remove();
  poiCluster = L.markerClusterGroup({ spiderfyOnMaxZoom: true, showCoverageOnHover: false });

  (data.features || []).forEach((f) => {
    const [gLon, gLat] = f.geometry.coordinates;
    const props = f.properties || {};
    const popupHtml = props.html_popup || props.popup_html || buildPoiPopup(props);
    const hasWiki = !!((props.wv || props.wiki)?.title);
    const icon = hasWiki ? poiGreenIcon : poiGrayIcon;
    const marker = L.marker([gLat, gLon], { icon }).bindPopup(popupHtml, {
      maxWidth: 420, // a bit wider like in your screenshot
      className: "wiki-popup",
    });
    poiCluster.addLayer(marker);
  });

  map.addLayer(poiCluster);
}

/* ---------------- API: Build Tour ---------------- */
async function buildTour() {
  const payload = {
    lat: lat.value, lon: lon.value,
    time_min: timeMin.value, radius_m: radius.value,
    roundtrip: tripMode.value === "round",
    end_lat: tripMode.value === "end" ? endLat : null,
    end_lon: tripMode.value === "end" ? endLon : null,
    router: "osrm", router_url: "http://osrm:5000", snap_path: true,
  };

  const { data } = await api.post("/api/tour", payload);

  if (tourLayer) tourLayer.remove();
  window._stopMarkers.forEach((m) => m.remove());
  window._stopMarkers = [];

  tourLayer = L.geoJSON(data.path, { style: { color: "#C42DE3", weight: 3.5, opacity: 1 } }).addTo(map);

  const stops = data.stops || [];
  stops.forEach((s, idx) => {
    if (idx === 0) {
      origin.setLatLng([s.lat, s.lon]);
    } else if (idx === stops.length - 1) {
      if (endMarker) endMarker.remove();
      endMarker = L.marker([s.lat, s.lon], { icon: endIcon, draggable: true }).addTo(map);
      endMarker.on("dragend", async (e) => {
        const c = e.target.getLatLng();
        endLat = c.lat; endLon = c.lng;
        await buildTour();
      });
      window._stopMarkers.push(endMarker);
    } else {
      const m = L.marker([s.lat, s.lon], { icon: midIcon }).addTo(map);
      window._stopMarkers.push(m);
    }
  });

  const b = tourLayer.getBounds();
  if (b.isValid()) map.fitBounds(b, { padding: [20, 20] });

  sheetState.value = "peek";
}

/* ---------------- route button ---------------- */
async function generateRoute() {
  if (isGenerating.value) return;
  isGenerating.value = true;
  try { await buildTour(); } finally { isGenerating.value = false; }
}

/* ---------------- map setup ---------------- */
onMounted(() => {
  const el = document.getElementById("map");
  if (el) el.style.height = "100%";

  map = L.map("map").setView([lat.value, lon.value], 14);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);

  origin = L.marker([lat.value, lon.value], { draggable: true, icon: startIcon }).addTo(map);
  origin.on("dragend", async (e) => {
    const c = e.target.getLatLng();
    lat.value = c.lat; lon.value = c.lng;
    circle.setLatLng(c);
    if (tourLayer) { tourLayer.remove(); tourLayer = null; }
    window._stopMarkers.forEach((m) => m.remove()); window._stopMarkers = [];
    await loadPois();
  });

  circle = L.circle([lat.value, lon.value], { radius: radius.value, fillOpacity: 0.15 , color: "#1BB9F5", weight: 2.9 }).addTo(map);
  loadPois();
});

onBeforeUnmount(() => {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  window.removeEventListener("touchmove", onPointerMove);
  window.removeEventListener("touchend", onPointerUp);
});

watch(radius, (v) => {
  if (circle) { circle.setRadius(v); loadPois(); }
});
</script>

<style>
html, body, #app { height: 100%; margin: 0; }
#map-container { position: relative; width: 100%; height: 100vh; overflow: hidden; }
#map { width: 100%; height: 100%; z-index: 1; }

/* Bottom sheet */
.bottom-sheet {
  position: absolute; right: 5%; bottom: 0; width: 90%;
  background: rgba(15, 22, 32, 0.48); color: #eef4ff;
  backdrop-filter: blur(2px) saturate(115%); -webkit-backdrop-filter: blur(2px) saturate(115%);
  border-radius: 14px 14px 0 0; box-shadow: 0 -10px 30px rgba(0,0,0,0.35);
  z-index: 1002; transition: transform 220ms ease; will-change: transform;
}

/* Drag handle */
.sheet-handle-area { width: 100%; height: 33px; display: flex; align-items: center; justify-content: center; cursor: grab; user-select: none; touch-action: pan-y; }
.sheet-handle-lines { display: flex; flex-direction: column; gap: 4px; align-items: center; }
.sheet-handle-lines span { display: block; width: 42px; height: 4px; border-radius: 4px; background: rgba(255,255,255,0.7); }

/* Content */
.sheet-content { padding: 6px 14px 14px; overflow: hidden; }
.panel-title { text-align: center; margin: 0 0 1px; font-weight: 444; font-size: 1rem; }

/* Dense layout */
.dense-grid { display: grid; grid-template-columns: 1fr; gap: 8px; }
.panel-section.compact { margin: 0; }
.label { font-size: .8rem; color: #d9e6ff; font-weight: 700; margin-bottom: 2px; }

/* Slider */
.cardish.compact { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 10px; padding: 8px 10px; }
.slider-row { display: flex; align-items: center; gap: 8px; }
.icon { font-size: 1.05rem; }
.horizontal-slider.slim { flex: 1; -webkit-appearance: none; height: 5px; border-radius: 4px; background: linear-gradient(90deg,#7f66ff 0%,#b06cff 100%); cursor: pointer; }
.horizontal-slider.slim::-webkit-slider-thumb,
.horizontal-slider.slim::-moz-range-thumb { width: 16px; height: 16px; border-radius: 50%; background: #fff; border: 2px solid #7f66ff; cursor: pointer; }
.slider-value { min-width: 56px; text-align: right; font-weight: 800; font-size: 0.9rem; }

/* Pills */
.row-two.compact { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.chk-pill.small {
  display: flex; align-items: center; gap: 6px; justify-content: center;
  background: linear-gradient(90deg,#eef 0%,#f6f0ff 100%);
  color: #4b3d8f; border-radius: 10px; padding: 8px 6px;
  font-weight: 700; font-size: 0.9rem; border: none;
}
.chk-pill.small input[type="radio"] { accent-color: #6a5cff; transform: scale(1.2); }
.option-icon { width: 18px; height: 18px; border-radius: 4px; object-fit: cover; }
.as-button { cursor: pointer; }
.as-button.full { width: 100%; }

/* Generate button */
.generate-btn {
  width: 100%; background: linear-gradient(135deg,#6a5cff 0%,#ff3db3 100%);
  color: white; border: none; border-radius: 12px; padding: 12px 0;
  font-size: 1.02rem; font-weight: 900; display: flex; align-items: center; justify-content: center; gap: 8px;
  cursor: pointer; box-shadow: 0 10px 24px rgba(0,0,0,0.35); transition: transform .1s ease, box-shadow .2s ease;
}
.generate-btn:hover { transform: translateY(-1px); box-shadow: 0 12px 28px rgba(0,0,0,0.45); }
.btn-icon { font-size: 1.1rem; }
.spinning { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* Advanced */
.adv-toggle { background: transparent; border: none; color: #d9e6ff; font-size: .9rem; text-decoration: underline; cursor: pointer; justify-self: start; }
.advanced-box { margin-top: 10px; }
.advanced-box h4 { margin: 0 0 6px 2px; }

/* Vertical actions */
.column-actions { display: flex; flex-direction: column; gap: 8px; }

/* Fade transition */
.fade-enter-active, .fade-leave-active { transition: opacity .2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }





</style>

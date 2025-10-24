<template>
  <div id="map-container">
    <div id="map"></div>

    <!-- LEFT: radius bar -->
    <div class="slider-container left">
      <span class="slider-icon">📏</span>
      <input
        type="range"
        v-model.number="radius"
        min="200"
        max="3000"
        step="50"
        class="slider-vertical"
        orient="vertical"
      />
      <span class="slider-value">{{ radius }} m</span>
    </div>

    <!-- RIGHT: time bar -->
    <div class="slider-container right">
      <span class="slider-icon">🕒</span>
      <input
        type="range"
        v-model.number="timeMin"
        min="10"
        max="180"
        step="5"
        class="slider-vertical"
        orient="vertical"
      />
      <span class="slider-value">{{ timeMin }} min</span>
    </div>

    <!-- CENTER: build route button -->
    <button class="route-btn" @click="buildTour">🔍</button>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue"
import axios from "axios"
import L from "leaflet"

const api = axios.create({ baseURL: "http://localhost:8000" })

// ---------- reactive state ----------
const timeMin = ref(60)
const radius = ref(700)
const lat = ref(59.3293)
const lon = ref(18.0686)

let map, origin, circle, poiLayer, tourLayer
let endMarker = null
let endLat = null
let endLon = null
window._stopMarkers = []

// ---------- icons ----------
const startIcon = L.icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  shadowSize: [41, 41],
})
const midIcon = L.icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  shadowSize: [41, 41],
})
const endIcon = L.icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  shadowSize: [41, 41],
})

// ---------- API ----------
async function loadPois() {
  const payload = {
    lat: lat.value,
    lon: lon.value,
    radius_m: radius.value,
    cat_weights: {},
  }
  const { data } = await api.post("/api/pois", payload)
  if (poiLayer) poiLayer.remove()
  poiLayer = L.geoJSON(data).addTo(map)
}

async function buildTour() {
  const payload = {
    lat: lat.value,
    lon: lon.value,
    time_min: timeMin.value,
    radius_m: radius.value,
    roundtrip: !endMarker,
    end_lat: endLat,
    end_lon: endLon,
    router: "osrm",
    router_url: "http://osrm:5000",
    snap_path: true,
  }

  console.log("Building route with payload:", payload)
  const { data } = await api.post("/api/tour", payload)

  // Clear old route
  if (poiLayer) poiLayer.remove()
  if (tourLayer) tourLayer.remove()
  window._stopMarkers.forEach((m) => m.remove())
  window._stopMarkers = []

  // Draw new route
  tourLayer = L.geoJSON(data.path, {
    style: { color: "blue", weight: 4, opacity: 0.9 },
  }).addTo(map)

  // Re-add origin
  if (origin) origin.addTo(map)

  // Add stops
  const stops = data.stops || []
  stops.forEach((s, idx) => {
    let marker
    if (idx === 0) {
      marker = origin
      marker.setLatLng([s.lat, s.lon])
    } else if (idx === stops.length - 1) {
      if (endMarker) endMarker.remove()
      endMarker = L.marker([s.lat, s.lon], {
        icon: endIcon,
        draggable: true,
      }).addTo(map)
      // recalc when end dragged
      endMarker.on("dragend", async (e) => {
        const c = e.target.getLatLng()
        endLat = c.lat
        endLon = c.lng
        await buildTour()
      })
      window._stopMarkers.push(endMarker)
    } else {
      marker = L.marker([s.lat, s.lon], { icon: midIcon })
      marker.addTo(map)
      window._stopMarkers.push(marker)
    }
  })

  // Fit map
  const bounds = tourLayer.getBounds()
  if (bounds.isValid()) map.fitBounds(bounds, { padding: [20, 20] })
}

// ---------- setup map ----------
onMounted(() => {
  map = L.map("map").setView([lat.value, lon.value], 14)
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map)

  // draggable start marker
  origin = L.marker([lat.value, lon.value], {
    draggable: true,
    icon: startIcon,
  }).addTo(map)

  origin.on("dragend", async (e) => {
    const c = e.target.getLatLng()
    lat.value = c.lat
    lon.value = c.lng
    circle.setLatLng(c)

    // Clear route and markers (but not end marker)
    if (tourLayer) {
      tourLayer.remove()
      tourLayer = null
    }
    window._stopMarkers.forEach((m) => m.remove())
    window._stopMarkers = []

    await loadPois()
  })

  circle = L.circle([lat.value, lon.value], {
    radius: radius.value,
    fillOpacity: 0.2,
  }).addTo(map)

  loadPois()
})

// ---------- watch ----------
watch(radius, (v) => {
  if (circle) {
    circle.setRadius(v)
    loadPois()
  }
})
</script>

<style>
#map-container {
  position: relative;
  width: 100%;
  height: 100%;
}
#map {
  width: 100%;
  height: 100%;
}

/* vertical slider containers */
.slider-container {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 66px;
  z-index: 1000;
  background: transparent;
  pointer-events: auto;
}
.slider-container.left {
  left: -46px;

}
.slider-container.right {
  right: -46px;
}

/* icon above slider */
.slider-icon {
  font-size: 1.3rem;
  margin-bottom: 6px;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);
}

/* slider element */
.slider-vertical {
  -webkit-appearance: none;
  appearance: none;
  transform: rotate(-90deg);
  width: 140px;
  height: 8px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 6px;
  outline: none;
  cursor: pointer;
  box-shadow: 0 0 3px rgba(0, 0, 0, 0.4);
  accent-color: #007bff;
  margin: 0;
}

.slider-vertical::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
}

/* value text below slider */
.slider-value {
  font-size: 0.9rem;
  font-weight: 700;
  color: rgb(190, 0, 0);
  margin-top: 4px;
  text-shadow: 0 0 5px rgb(255, 255, 255);
}

/* central route button */
.route-btn {
  position: absolute;
  bottom: 5px;
  left: 50%;
  transform: translateX(-50%);
  background: #4caf50;
  color: white;
  border: none;
  font-size: 1.4rem;
  border-radius: 50%;
  width: 52px;
  height: 52px;
  cursor: pointer;
  z-index: 1001;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.35);
  opacity: 0.92;
}
.route-btn:hover {
  background: #45a049;
}
</style>

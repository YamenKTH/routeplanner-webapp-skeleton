<template>
  <div id="map-container">
    <div id="map"></div>

    <!-- Navigation Banner (Google Maps style) -->
    <div
      v-if="confirmedRoute && !isRoutePlanningMode && (isArrived || currentNavInfo)"
      class="nav-banner"
    >
      <!-- Show deviation warning if off-route -->
      <div v-if="!isArrived && currentNavInfo && currentNavInfo.isOffRoute" class="nav-deviation-warning">
        <div class="nav-deviation-icon">⚠️</div>
        <div class="nav-deviation-text">
          <div class="nav-deviation-title">Off Route</div>
          <div class="nav-deviation-distance">
            {{ currentNavInfo ? formatDistance(currentNavInfo.deviationFromRoute) : '' }} from route
          </div>
        </div>
      </div>
      
      <div class="nav-banner-content">
        <!-- ARRIVED -->
        <template v-if="isArrived">
          <div class="nav-distance-main">
            <div class="nav-destination">You've arrived at {{ currentPoiName }}</div>
          </div>
        </template>

        <template v-else>
          <!-- Prioritize turn instruction when close (within 300m) -->
          <template v-if="currentNavInfo && currentNavInfo.nextTurn && !currentNavInfo.isOffRoute && currentNavInfo.nextTurn.distance_m <= 300">
            <div class="nav-turn-main">
              <div class="nav-turn-instruction-text">
                {{ currentNavInfo.nextTurn.direction }} in {{ formatDistance(currentNavInfo.nextTurn.distance_m) }}
              </div>
              <div v-if="currentNavInfo.nextTurn.time_s" class="nav-turn-time">
                approx {{ formatTime(currentNavInfo.nextTurn.time_s) }} walking
              </div>
            </div>
            <div class="nav-to-destination">
              <span class="nav-destination-label">Total distance to {{ currentNavInfo.nextStopName }}:</span>
              <span class="nav-destination-distance">{{ formatDistance(currentNavInfo.distance_m) }}</span>
            </div>
          </template>

          <!-- Otherwise show distance to POI as primary -->
          <template v-else>
            <div class="nav-distance-main">
              <div
                class="nav-distance"
                :class="{ 'off-route-distance': currentNavInfo && currentNavInfo.isOffRoute }"
              >
                {{ currentNavInfo ? formatDistance(currentNavInfo.distance_m) : '' }}
              </div>
              <div class="nav-destination">{{ currentNavInfo ? currentNavInfo.nextStopName : '' }}</div>
              <div v-if="currentNavInfo && currentNavInfo.time_s" class="nav-time">
                {{ formatTime(currentNavInfo.time_s) }} walking
              </div>
            </div>

            <!-- Show upcoming turn as secondary info if available -->
            <div
              v-if="currentNavInfo && currentNavInfo.nextTurn && !currentNavInfo.isOffRoute"
              class="nav-turn-upcoming"
            >
              <div class="nav-turn-instruction-text">
                {{ currentNavInfo.nextTurn.direction }} in {{ formatDistance(currentNavInfo.nextTurn.distance_m) }}
              </div>
              <div v-if="currentNavInfo.nextTurn.time_s" class="nav-turn-time">
                approx {{ formatTime(currentNavInfo.nextTurn.time_s) }} walking
              </div>
            </div>
          </template>
        </template>

        <!-- Manual Mode Indicator -->
        <div v-if="isManualMode" class="nav-manual-mode-indicator">
          <span class="manual-mode-icon">✋</span>
          <span class="manual-mode-text">Manual mode - drag marker to simulate</span>
          <button class="manual-mode-reset-btn" @click="resetToGPSLocation">Use GPS</button>
        </div>
      </div>
    </div>

    <!-- Location Buttons -->
    <div class="location-buttons">
      <button class="location-btn" @click="useMyLocation" title="My Location">
        📡
        <span class="location-btn-tooltip">My Location</span>
      </button>
      <button v-if="confirmedRoute && !isRoutePlanningMode && currentLocationMarker" 
              class="location-btn" 
              :class="{ 'loading': isResettingGPS }"
              @click="resetToGPSLocation"
              :disabled="isResettingGPS"
              title="Reset to GPS">
        <span v-if="isResettingGPS" class="spinner">⏳</span>
        <span v-else>🔄</span>
        <span class="location-btn-tooltip">Reset to GPS</span>
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

          <!-- Top bar: stats + tiny browse arrows (top-right) -->
          <div class="route-summary">
            <div class="route-stats">
              <span class="stat">📍 {{ confirmedRoute.stops.length }} stops</span>
              <span class="stat">📏 {{ confirmedRoute.distance }} km</span>
              <span class="stat">🕒 {{ confirmedRoute.time }}</span>
            </div>

            <!-- Tiny arrows in top-right -->
            <div class="poi-browse-controls">
              <button class="browse-btn" @click="prevPoi" :disabled="currentPoiIndex === 0">◀</button>
              <button class="browse-btn" @click="nextPoi" :disabled="currentPoiIndex === confirmedRoute.stops.length - 1">▶</button>
            </div>
          </div>

          <!-- NAVIGATING: sneak peek of NEXT stop + "I'm here" -->
          <div v-if="!isArrived" class="nav-mode navigating">

            <!-- A) Current destination: LIMITED -->
            <template v-if="currentPoiIndex === destIndex">
              <div class="next-peek">
                <div class="peek-label">Current destination</div>
                <div class="peek-title"
                    :style="{ opacity: visitedIdx.has(currentPoiIndex) ? 0.45 : 1 }">
                  {{ currentPoiName }}
                </div>
              </div>

              <!-- Actions: now together -->
              <div class="poi-quick-actions tight">
                <button class="action primary" @click="onImHereClick">✅ I’m here</button>
                <button class="action danger"  @click="cancelNavigation">Cancel</button>
              </div>
            </template>


            <!-- B) Old (visited) stop: FULL TEXT -->
            <template v-else-if="visitedIdx.has(currentPoiIndex)">
              <div class="current-poi-card">
                <h4 :style="{ opacity: 0.6 }">{{ currentPoiName }}</h4>
                <div class="poi-details">
                  <div class="poi-info" v-if="currentPoiDetails">
                    <div class="poi-categories">{{ currentPoiDetails.categories }}</div>
                    <div class="poi-description">{{ currentPoiDetails.description }}</div>
                  </div>
                </div>
                <!-- no Next button here (still in navigating mode) -->
              </div>
            </template>

            <!-- C) Future stop (after destination): FULL TEXT -->
            <template v-else>
              <div class="current-poi-card">
                <h4>{{ currentPoiName }}</h4>
                <div class="poi-details">
                  <div class="poi-info" v-if="currentPoiDetails">
                    <div class="poi-categories">{{ currentPoiDetails.categories }}</div>
                    <div class="poi-description">{{ currentPoiDetails.description }}</div>
                  </div>
                </div>
              </div>
            </template>

          </div>

          <!-- ARRIVED: full current POI + "Next stop →" -->
          <div v-else class="nav-mode arrived">
            <div class="current-poi-card">
              <h4 :style="{ opacity: 1 }">
                {{ currentPoiName }}
              </h4>
              <div class="poi-details">
                <div class="poi-info" v-if="currentPoiDetails">
                  <!--<div class="poi-categories">{{ currentPoiDetails.categories }}</div>-->
                  <div class="poi-description">{{ currentPoiDetails.description }}</div>
                </div>
              </div>
              <div class="poi-navigation-footer">
                <button
                  class="nav-btn next"
                  @click="onArrivedPrimaryAction"
                  :disabled="currentPoiIndex !== furthestVisitedIndex">
                  {{ currentPoiIndex === confirmedRoute.stops.length - 1 ? 'End tour' : 'Next stop →' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Keep: Cancel Navigation -->
          <button v-if="isArrived" class="cancel-nav-btn" @click="cancelNavigation">
            Cancel Navigation
          </button>
        </div>
        
        <!-- POI DETAILS VIEW (opens when a map marker is clicked) -->
        <!-- POI DETAILS VIEW -->
        <div
          v-else-if="selectedPoi"
          class="poi-details-sheet"
          :class="{ expanded: showFullExtract }"
        >

          <!-- Sticky Header -->
          <div class="poi-sheet-header">
            <h3 class="panel-title">{{ selectedPoi.name || 'Place' }}</h3>
            <button class="close-sheet-btn" @click="clearSelectedPoi">✕</button>
          </div>

          <!-- Scrollable Body -->
          <div class="poi-scroll">
            <div class="poi-meta">
              <div class="poi-line">
              </div>
            <div class="poi-extract" :class="{ clamped: shouldClamp && !showFullExtract }">
              {{ selectedPoi.extractFull }}
            </div>

              <!-- Inline actions (old Read more style + Open article, separated by •) -->
              <div class="read-actions">
                <template v-if="shouldClamp">
                  <button class="text-link" @click="onToggleReadMore">
                    {{ showFullExtract ? 'Show less' : 'Read more' }}
                  </button>
                </template>

                <template v-if="(selectedPoi.wv?.project && selectedPoi.wv?.title)">
                  <span class="sep" v-if="shouldClamp">•</span>
                  <a
                    :href="`https://${selectedPoi.wv.project}/wiki/${selectedPoi.wv.title}`"
                    target="_blank"
                    class="text-link"
                  >
                    Open article
                  </a>
                </template>

                <!-- Views + score -->
                <span class="views" v-if="selectedPoi.wv">
                  📖 {{ (selectedPoi.wv.views_365 || 0).toLocaleString() }} views
                  <span v-if="selectedPoi.devScore !== null">
                    &nbsp;•&nbsp;⭐ {{ Number(selectedPoi.devScore).toFixed(2) }}
                  </span>
                </span>

                <!-- Categories last - (truncated in compact, full when expanded) -->
                <div
                  v-if="(selectedPoi.kindsArr || []).length"
                  class="categories-line"
                  :class="{ clamped: !showFullExtract }"
                >
                  <strong>Categories:</strong>
                  {{ (showFullExtract ? selectedPoi.kindsArr : selectedPoi.kindsArr.slice(0, 6)).join(', ') }}
                </div>
              </div>

              

            </div>
              <!-- Docked Footer (always same place) -->
            <div class="poi-actions docked">
              <button
                v-if="isPoiInActiveRoute(selectedPoi)"
                class="action danger"
                @click="removePoiFromRoute(selectedPoi)"
              >
                ➖ Remove from route
              </button>

              <button
                v-else
                class="action primary"
                @click="addPoiToRoute(selectedPoi)"
              >
                ➕ Add to route
              </button>

              <div class="row" v-if="showStartEnd">
                <button class="action" @click="setAsStart(selectedPoi.lat, selectedPoi.lon)">Start</button>
                <button class="action danger" @click="setAsEnd(selectedPoi.lat, selectedPoi.lon)">End</button>
              </div>
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
            <button class="generate-new-route-btn" @click="goBackToPlanning">
              ↻ Generate New Route
            </button>
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
                  <div class="poi-desc" v-if="stop.description" style="font-size: .85rem; opacity: .9; margin-top: 2px; line-height: 1.25;">
                    {{ stop.description.length > 180 ? (stop.description.slice(0, 180) + '…') : stop.description }}
                  </div>
                  <div class="poi-meta" style="margin-top: 4px; font-size: .75rem; opacity: .85; display: flex; gap: 8px; align-items: center;">
                    <span v-if="typeof stop.views_365 === 'number'">📖 {{ stop.views_365.toLocaleString() }}</span>
                    <a v-if="stop.wiki_url" :href="stop.wiki_url" target="_blank" style="color:#6a5cff; text-decoration: none;">Open article ↗</a>
                  </div>
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
            <!-- Time temp -->
            <div class="panel-section compact">
              <div class="time-card time-compact cardish compact">
                <div class="time-header">
                  <span class="time-title-compact">Select <strong>End Time:</strong></span>
                  <input type="time" class="time-time large" v-model="endTimeStr" step="300" />
                </div>

                <div class="time-subline">
                  <span>Start {{ startTimeStr }}</span>
                  <span>•</span>
                  <span>{{ durationPretty }}</span>
                </div>
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
              Customize more
            </button>
          </div>

          <!-- ADVANCED -->
          <transition name="fade">
            <div v-if="sheetState==='expanded'" class="advanced-box">
              <h4>Customize more</h4>
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

// --- Navigation experiment flags & thresholds ---
const NAV_EXPERIMENT_ON = true;

const PATH_TOL = 10;               // meters: consider "on the path" if ≤ this
const DEVIATION_THRESHOLD = 30;    // meters: show Off Route if > this (reroute later)
const ON_PATH_FOR_DISTANCE_TOL = DEVIATION_THRESHOLD; // 30 m is a good start


const ARRIVAL_RADIUS = 12;       // meters remaining along path to count as arrived
const ARRIVAL_DEBOUNCE_S = 1;    // seconds of sustained proximity


const arrivalCandidateStartedAt = ref(null);
const poiIndexChangeReason = ref('auto'); // 'auto' | 'manual'

const autoAdvanceEnabled = ref(true); // toggle if you ever want to disable auto-advance
const _walkProbe = ref({
  active: false,
  prevDist: null,
  improvingTicks: 0,
  basePos: null,
  baseDist: null,
});


// --- New tour state (JS) ---
const navMode = ref('navigating');      // 'navigating' or 'arrived'
const visitedIdx = ref(new Set());      // Set of visited stop indexes

const isArrived = computed(() => navMode.value === 'arrived');

//auto advance:
const _departProbe = ref({
  active: false,
  base_m: null,     // distance to next stop at the moment we arrived
  last_m: null,
  consecTicks: 0,
});

const DEPART_TOTAL_DELTA = 15;   // meters closer overall to trigger
//const MIN_STEP_GAIN      = 2.5;  // must improve at least this much per tick
const MIN_CONSEC_TICKS   = 2;    // ...for this many consecutive ticks
const JITTER_TOL             = 1.5;

// The stop we’re currently walking to = destination of the active leg
const destIndex = computed(() => {
  const n = confirmedRoute.value?.stops?.length || 0;
  if (!n) return null;
  return Math.min((currentNavLegIndex.value || 0) + 1, n - 1);
});

const furthestVisitedIndex = computed(() => {
  if (!visitedIdx.value || visitedIdx.value.size === 0) return -1;
  let max = -1;
  for (const i of visitedIdx.value) if (i > max) max = i;
  return max;
});

const nextPoiIndex = computed(() => {
  if (!confirmedRoute.value || !confirmedRoute.value.stops?.length) return null;
  const i = Math.min(currentPoiIndex.value + 1, confirmedRoute.value.stops.length - 1);
  return i === currentPoiIndex.value ? null : i;
});

// Show the next POI title in the sneak peek
const nextPoiTitle = computed(() => {
  const i = nextPoiIndex.value;
  if (i == null) return null;
  const stop = confirmedRoute.value?.stops?.[i];
  return stop?.name || `Stop ${i + 1}`;
});

// Prevent teleporting when browsing POIs with the tiny arrows
const teleportOnManualJump = ref(false);


function distToNextStopWalking_m() {
  const iNext = nextPoiIndex.value;
  if (iNext == null || !currentGPSPosition.value) return Infinity;

  const [clat, clon] = currentGPSPosition.value;
  const nextStop = confirmedRoute.value?.stops?.[iNext];
  if (!nextStop) return Infinity;

  // Prefer along the NEXT leg if we’re near it
  const leg = confirmedRoute.value?.navigation_legs?.[iNext - 1];
  const legLen = Number(leg?.distance_m) || 0;

  if (leg && Array.isArray(leg.coords_latlon) && leg.coords_latlon.length > 1) {
    if (!leg._cum || !leg._segLen) {
      const { cum, segLen } = buildCumMeasures(leg.coords_latlon);
      leg._cum = cum; leg._segLen = segLen;
    }
    const snap = projectToPolyline([clat, clon], leg.coords_latlon, leg._cum, leg._segLen);
    // if you’re within 30 m of the next leg, use along-route; else fallback to straight-line
    if (snap && snap.distanceToPath_m <= 30 && Number.isFinite(snap.measure_m)) {
      return Math.max(0, legLen - snap.measure_m);
    }
  }

  // fallback: straight-line distance
  return haversineDistance(clat, clon, nextStop.lat, nextStop.lon);
}

function remainingToNextStopMeters() {
  const iNext = nextPoiIndex.value;
  if (iNext == null) return Infinity;
  if (!currentGPSPosition.value) return Infinity;

  const [clat, clon] = currentGPSPosition.value;
  const nextStop = confirmedRoute.value?.stops?.[iNext];
  if (!nextStop) return Infinity;

  // Prefer along-route distance on the NEXT leg (iNext - 1)
  const leg = confirmedRoute.value?.navigation_legs?.[iNext - 1];
  const legLen = Number(leg?.distance_m) || 0;

  if (leg && Array.isArray(leg.coords_latlon) && leg.coords_latlon.length > 1) {
    // ensure cum/segLen
    if (!leg._cum || !leg._segLen) {
      const { cum, segLen } = buildCumMeasures(leg.coords_latlon);
      leg._cum = cum; leg._segLen = segLen;
    }
    const snap = projectToPolyline([clat, clon], leg.coords_latlon, leg._cum, leg._segLen);
    // if we’re reasonably near the next leg, use along-route remaining; else fall back to straight-line
    const NEAR_NEXT_LEG_TOL = 40; // meters
    if (snap && Number.isFinite(snap.measure_m) && snap.distanceToPath_m <= NEAR_NEXT_LEG_TOL) {
      return Math.max(0, legLen - snap.measure_m);
    }
  }

  // Fallback: straight-line to next POI
  console.log("FELL BACK ON HAVERSINE -- BAD")
  return haversineDistance(clat, clon, nextStop.lat, nextStop.lon);
}


function onArrivedPrimaryAction() {
  // Only act at the latest arrived stop (prevents skipping when browsing back)
  if (currentPoiIndex.value !== furthestVisitedIndex.value) {
    toast("⏪ You’re viewing an earlier stop");
    return;
  }

  const last = (confirmedRoute.value?.stops?.length || 1) - 1;
  if (currentPoiIndex.value === last) {
    // Final stop: end as you do today
    cancelNavigation();
    toast("🏁 Tour finished");
  } else {
    // Otherwise: continue exactly as before
    goToNextStop();
  }
}

function maybeAutoDepartFromArrived() {
  if (navMode.value !== 'arrived') return;
  if (!_departProbe.value.active) return;
  const ALLOW_MANUAL_DEPART = true;           //NOT SURE IF WANT!!!
  //if (isManualMode.value) return; // don’t trigger while dragging REMOVED!
  if (isManualMode.value && !ALLOW_MANUAL_DEPART) return;


  const iNext = nextPoiIndex.value;
  if (iNext == null) return;

  const dNow = distToNextStopWalking_m();
  if (!Number.isFinite(dNow)) return;

  const P = _departProbe.value;
  if (P.last_m == null) {
    P.last_m = dNow;
    return;
  }

  const stepGain = P.last_m - dNow; // positive if moving closer this tick
  if (Math.abs(stepGain) > JITTER_TOL) {
    P.consecTicks = stepGain > 0 ? P.consecTicks + 1 : Math.max(0, P.consecTicks - 1);
  }


  P.last_m = dNow;

 // Trigger once we are ≥ 15m closer than where we started (baseline)
  if (Number.isFinite(P.base_m)) {
    const deltaFromBase = P.base_m - dNow; // >= 15 => left toward next POI
    if (deltaFromBase >= DEPART_TOTAL_DELTA && P.consecTicks >= MIN_CONSEC_TICKS) {
      startNavigatingTo(iNext);
      const nextName = confirmedRoute.value?.stops?.[iNext]?.name || `Stop ${iNext + 1}`;
      toast(`➡️ Heading to ${nextName}`);
      P.active = false;
    }
  }

}

// mark current stop as arrived
function markArrived(manual) {
  if (!confirmedRoute.value?.stops?.length) return;
  const s = new Set(visitedIdx.value);
  s.add(currentPoiIndex.value);
  visitedIdx.value = s;
  navMode.value = 'arrived';

  // reset walk probe and start depart probe
  _walkProbe.value   = { active: false, prevDist: null, improvingTicks: 0, basePos: null, baseDist: null };
  const dBase = distToNextStopWalking_m(); // uses next leg when close, falls back to straight line
  _departProbe.value = { active: true, base_m: Number.isFinite(dBase) ? dBase : null, last_m: null, consecTicks: 0 };

  if (manual) toast("📍 Marked as arrived");
}
// start navigating to a given stop index (or keep current)
function startNavigatingTo(index) {
  if (!confirmedRoute.value?.stops?.length) return;

  if (Number.isFinite(index)) {
    const maxPoi = confirmedRoute.value.stops.length - 1;
    const newIndex = clamp(index, 0, maxPoi);

    currentPoiIndex.value = newIndex;

    // ✅ leg that goes TO stop newIndex is (newIndex - 1)
    const maxLeg = (confirmedRoute.value.navigation_legs?.length || 1) - 1;
    currentNavLegIndex.value = Math.max(0, Math.min(newIndex - 1, maxLeg));
  }

  navMode.value = 'navigating';
  _walkProbe.value = { active: false, prevDist: null, improvingTicks: 0, basePos: null, baseDist: null };
}
function goToNextStop() {
  if (!confirmedRoute.value?.stops?.length) return;

  // Only allow if we're at the latest arrived stop
  if (currentPoiIndex.value !== furthestVisitedIndex.value) {
    toast("⏪ You’re viewing an earlier stop");
    return;
  }

  const i = currentPoiIndex.value + 1;
  if (i < confirmedRoute.value.stops.length) {
    startNavigatingTo(i);               // this set leg = i-1 (we already fixed)
  } else {
    toast("🎉 Route complete!");
  }
}

// Button handler we’ll wire in Step 2
function onImHereClick() { markArrived(true); }


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

//POI read in bottom sheet:
const selectedPoi = ref(null);  // NEW STATE: When we have selected a POI and want to read about it. 
const showFullExtract = ref(false);
const shouldClamp = computed(() => (selectedPoi.value?.extractFull?.length || 0) > 300);
let currentSelectedMarker = null;


// End position management
const endPositionSelected = ref(false);
const endLat = ref(null);
const endLon = ref(null);

let map, origin, circle, poiCluster, tourLayer;
let currentLegLayer = null; // Highlighted layer for current leg to next POI
let deviationLineLayer = null; // Line from user position to nearest route point when off-route
let endMarker = null;
const candidateEnd = ref(null);
let tempEndMarker = null;
window._stopMarkers = [];

// Track route POIs to avoid duplicates
let routePoiMarkers = [];

// Live navigation tracking
let geoWatchId = null;
let currentLocationMarker = null;
const isManualMode = ref(false); // Flag to pause GPS updates when manually dragging
const currentGPSPosition = ref(null); // Track current GPS position [lat, lon]
const currentNavLegIndex = ref(0); // Track which navigation leg we're currently on (starts at 0)
const isResettingGPS = ref(false); // Loading state for reset GPS button

/* ---------------- computed properties ---------------- */
const canGenerate = computed(() => {
  if (tripMode.value === "round") return true;
  return endPositionSelected.value && !!endLat.value && !!endLon.value;
});

const currentRoute = computed(() => {
  const route = generatedRoutes.value[currentRouteIndex.value];
  if (!route) {
    console.warn(' WARNING: currentRoute is undefined – no generated route found');
    return { stops: [], navigation_legs: [] };
  }
  return route;
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

const showStartEnd = computed(() => {
  // Only in initial planning view (before route generation)
  return isRoutePlanningMode.value && !selectedEndStart.value;
});

// --- after other refs/computeds ---
const activeRoute = computed(() => {
  // During route-selection, use the currently browsed candidate
  if (isRoutePlanningMode.value && selectedEndStart.value) return currentRoute.value;
  // Otherwise, if we have a confirmed route (navigation/planning), use it
  if (confirmedRoute.value) return confirmedRoute.value;
  return null;
});

// prefer xid; fall back to lat/lon/name matching
function poiKey(p) {
  if (p?.xid) return `xid:${p.xid}`;
  const lat = Number(p?.lat ?? p?.geometry?.coordinates?.[1]);
  const lon = Number(p?.lon ?? p?.geometry?.coordinates?.[0]);
  if (Number.isFinite(lat) && Number.isFinite(lon)) return `ll:${lat.toFixed(6)},${lon.toFixed(6)}`;
  return `name:${(p?.name || '').toLowerCase()}`;
}

/**function isPoiInActiveRoute(poi) {
  const r = activeRoute.value;
  if (!r?.stops?.length) return false;
  const k = poiKey(poi);
  return r.stops.some(s => poiKey(s) === k);
}**/


// ----- Geometry helpers for accurate path snapping -----

// Fast local projection (meters) using equirectangular approx around a ref lat
function _toXY(lat, lon, refLat) {
  const R = 6371000; // m
  const phi = refLat * Math.PI / 180;
  const x = (lon * Math.PI / 180) * Math.cos(phi) * R;
  const y = (lat * Math.PI / 180) * R;
  return [x, y];
}

// Build cumulative meters per vertex and segment lengths for a polyline of [lat,lon]
function buildCumMeasures(polyLatLon) {
  const n = Array.isArray(polyLatLon) ? polyLatLon.length : 0;
  const cum = new Array(n).fill(0);
  const segLen = new Array(Math.max(n - 1, 0)).fill(0);
  if (n <= 1) return { cum, segLen };

  const refLat = polyLatLon[0][0];
  let prev = _toXY(polyLatLon[0][0], polyLatLon[0][1], refLat);
  for (let i = 1; i < n; i++) {
    const cur = _toXY(polyLatLon[i][0], polyLatLon[i][1], refLat);
    const dx = cur[0] - prev[0];
    const dy = cur[1] - prev[1];
    const d = Math.hypot(dx, dy);
    segLen[i - 1] = d;
    cum[i] = cum[i - 1] + d;
    prev = cur;
  }
  return { cum, segLen };
}

// Project a point to the closest point on the polyline (segment-wise, clamped)
// Returns: { snappedLat, snappedLon, distanceToPath_m, measure_m, segIndex, t }
function projectToPolyline(pointLatLon, polyLatLon, cum, segLen) {
  const n = Array.isArray(polyLatLon) ? polyLatLon.length : 0;
  if (n === 0) {
    return {
      snappedLat: pointLatLon[0], snappedLon: pointLatLon[1],
      distanceToPath_m: Infinity, measure_m: 0, segIndex: -1, t: 0
    };
  }
  if (n === 1) {
    // Snap to the only vertex
    const [pLat, pLon] = pointLatLon;
    const [vLat, vLon] = polyLatLon[0];
    const d = haversineDistance(pLat, pLon, vLat, vLon);
    return {
      snappedLat: vLat, snappedLon: vLon,
      distanceToPath_m: d, measure_m: 0, segIndex: 0, t: 0
    };
  }

  const refLat = polyLatLon[0][0];
  const [px, py] = _toXY(pointLatLon[0], pointLatLon[1], refLat);

  let best = { dist2: Infinity, segIndex: 0, t: 0, sx: 0, sy: 0 };
  let ax = 0, ay = 0, bx = 0, by = 0;

  // Iterate segments i:(Vi -> Vi+1)
  for (let i = 0; i < n - 1; i++) {
    if (segLen[i] === 0) continue;

    if (i === 0) {
      [ax, ay] = _toXY(polyLatLon[0][0], polyLatLon[0][1], refLat);
    } else {
      ax = bx; ay = by;
    }
    [bx, by] = _toXY(polyLatLon[i + 1][0], polyLatLon[i + 1][1], refLat);

    const vx = bx - ax, vy = by - ay;
    const v2 = vx * vx + vy * vy;
    let t = ((px - ax) * vx + (py - ay) * vy) / v2;
    t = Math.max(0, Math.min(1, t));
    const sx = ax + t * vx, sy = ay + t * vy;
    const dx = px - sx, dy = py - sy;
    const dist2 = dx * dx + dy * dy;

    if (dist2 < best.dist2) best = { dist2, segIndex: i, t, sx, sy };
  }

  // Convert snapped back to lat/lon
  const snappedLat = (best.sy / 6371000) * (180 / Math.PI);
  const snappedLon = (best.sx / (6371000 * Math.cos(refLat * Math.PI / 180))) * (180 / Math.PI);
  const distanceToPath_m = Math.sqrt(best.dist2);

  // Along-path measure = cum at seg start + t * segLen
  const measure_m = (cum[best.segIndex] || 0) + best.t * (segLen[best.segIndex] || 0);

  return { snappedLat, snappedLon, distanceToPath_m, measure_m, segIndex: best.segIndex, t: best.t };
}

//____________________________________________________________________________________________

// Haversine distance calculation (in meters)
function haversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000; // Earth radius in meters
  const phi1 = lat1 * Math.PI / 180;
  const phi2 = lat2 * Math.PI / 180;
  const dPhi = (lat2 - lat1) * Math.PI / 180;
  const dLambda = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dPhi / 2) * Math.sin(dPhi / 2) +
            Math.cos(phi1) * Math.cos(phi2) *
            Math.sin(dLambda / 2) * Math.sin(dLambda / 2);
  return 2 * R * Math.asin(Math.sqrt(a));
}



const currentNavInfo = computed(() => {
  if (!confirmedRoute.value || isRoutePlanningMode.value || !currentGPSPosition.value) return null;
  if (navMode.value === 'arrived') return null;
  
  const stops = confirmedRoute.value.stops || [];
  const navLegs = confirmedRoute.value.navigation_legs || [];
  
  if (stops.length === 0 || navLegs.length === 0) return null;
  
  // Ensure currentNavLegIndex is within valid range
  const legIndex = Math.max(0, Math.min(currentNavLegIndex.value, navLegs.length - 1));

  if (!window.__lastLegIndex) window.__lastLegIndex = legIndex;
  if (window.__lastLegIndex !== legIndex) {
    if (window.__legProg) delete window.__legProg[`leg:${window.__lastLegIndex}`];
    if (window.__navProgS) window.__navProgS.prev = null;
    window.__lastLegIndex = legIndex;
  }
  
  // Get the leg information
  try {
    const legs = confirmedRoute.value?.navigation_legs || [];
    for (const leg of legs) {
      if (Array.isArray(leg?.coords_latlon) && leg.coords_latlon.length >= 1) {
        const { cum, segLen } = buildCumMeasures(leg.coords_latlon);
        leg._cum = cum;
        leg._segLen = segLen;
      } else {
        leg._cum = []; 
        leg._segLen = [];
      }
    }
  } catch (e) {
    console.warn('cum/seg precompute failed', e);
  }
  const leg = navLegs[legIndex];
  if (!leg) return null;
  const legLen = Number(leg.distance_m) || 0;

  function parseManeuver(step) {
    // Accept object or string
    if (step && typeof step.maneuver === 'object' && step.maneuver) {
      const type = (step.maneuver.type || '').toLowerCase();
      const mod  = (step.maneuver.modifier || '').toLowerCase();
      const loc  = step.maneuver.location; // [lon, lat]
      return { type, modifier: mod, location: loc };
    }
    const mStr = String(step?.maneuver || '').toLowerCase();
    const [type, mod = ''] = mStr.includes(':') ? mStr.split(':') : [mStr, ''];
    return { type: type.trim(), modifier: mod.trim(), location: step?.maneuver_location };
  }

  // -- map step starts to meters along the polyline using the maneuver location
  function stepStartMeters(leg, step, accFallback) {
    // OSRM maneuver location is [lon, lat]
    const { location: loc } = parseManeuver(step);
    if (Array.isArray(loc) && loc.length === 2
        && Array.isArray(leg.coords_latlon) && leg.coords_latlon.length > 0) {
      const [lon, lat] = loc;
      const snap = projectToPolyline([lat, lon], leg.coords_latlon, leg._cum || [], leg._segLen || []);
      if (snap && Number.isFinite(snap.measure_m)) return snap.measure_m;
    }
    // fallback if location missing
    return accFallback;
  }

  let acc = 0;
  const stepsResolved = (leg.steps || []).map((s) => {
    const startByAcc = acc;
    acc += Number(s.distance_m) || 0;
    return { ...s, _start_m: stepStartMeters(leg, s, startByAcc) };
  });
  // sort in case projections reorder slightly
  stepsResolved.sort((a, b) => (a._start_m || 0) - (b._start_m || 0));

  leg._stepsResolved = stepsResolved;
  
  const [currentLat, currentLon] = currentGPSPosition.value;
  
  const nextStopIndex = legIndex + 1;
  const nextStop = stops[nextStopIndex];
  const nextStopName = nextStop?.name || `Stop ${nextStopIndex + 1}`;
  
  let deviationFromRoute = Infinity;
  let traveledDistance = 0;
  let nearestRoutePoint = null;

  if (Array.isArray(leg.coords_latlon) && leg.coords_latlon.length > 0 && NAV_EXPERIMENT_ON) {
    const { snappedLat, snappedLon, distanceToPath_m, measure_m } =
      projectToPolyline([currentLat, currentLon], leg.coords_latlon, leg._cum || [], leg._segLen || []);

    deviationFromRoute = distanceToPath_m;
    //traveledDistance   = measure_m;
    nearestRoutePoint  = [snappedLat, snappedLon];

    // --- NEW: cap/monotonic progress per leg ---
    if (!window.__legProg) window.__legProg = {};
    const progKey = `leg:${legIndex}`;
    const prev = window.__legProg[progKey]?.prev ?? 0;

    // avg speed for caps
    const speedMps = (leg.duration_s && leg.distance_m > 0)
      ? (leg.distance_m / leg.duration_s)
      : 1.35;

    // allow bigger jumps when dragging than GPS
    const maxFwd  = isManualMode.value ? 40 : Math.max(10, speedMps * 2.0); // meters per update
    const maxBack = 10;                                                     // meters

    let prog_m = measure_m;

    // cap forward & backward motion
    prog_m = Math.min(prog_m, prev + maxFwd);
    prog_m = Math.max(prog_m, prev - maxBack);

    // keep inside leg
    
    prog_m = Math.max(0, Math.min(prog_m, legLen));

    // persist & use as traveledDistance
    window.__legProg[progKey] = { prev: prog_m };
    traveledDistance = prog_m;


  } else {
    // fallback to old vertex-nearest behavior
    let minDist = Infinity, idx = 0;
    for (let i = 0; i < leg.coords_latlon.length; i++) {
      const [plat, plon] = leg.coords_latlon[i];
      const d = haversineDistance(currentLat, currentLon, plat, plon);
      if (d < minDist) { minDist = d; idx = i; }
    }
    deviationFromRoute = minDist;
    // coarse cumulative
    for (let i = 1; i <= idx && i < leg.coords_latlon.length; i++) {
      const [lat1, lon1] = leg.coords_latlon[i - 1];
      const [lat2, lon2] = leg.coords_latlon[i];
      traveledDistance += haversineDistance(lat1, lon1, lat2, lon2);
    }
    nearestRoutePoint = leg.coords_latlon[idx] || null;
  }
    
  
  traveledDistance = Math.max(0, Math.min(traveledDistance || 0, legLen));
  // Calculate remaining distance to next stop
  // If on-route (within threshold), use route-based distance; otherwise use direct distance
  let remainingDistance = Number(legLen) || 0;
  
  if (leg.coords_latlon && leg.coords_latlon.length > 0 && nextStop) {
    const directDistance = haversineDistance(currentLat, currentLon, nextStop.lat, nextStop.lon);
    if (deviationFromRoute <= ON_PATH_FOR_DISTANCE_TOL) {
      // Prefer along-route distance while we’re reasonably close to the path
      const remainingRouteDistance = Math.max(0, legLen - (traveledDistance || 0));
      remainingDistance = remainingRouteDistance;
    } else {
      // Far from path → fall back to straight-line until we re-snap / reroute
      remainingDistance = directDistance;
    }
  } else if (nextStop) {
     // Fallback: use direct distance if no route coordinates
     remainingDistance = haversineDistance(currentLat, currentLon, nextStop.lat, nextStop.lon);
   }
    
  
  // Find the next turn/step based on user's position
  let nextTurn = null;
  

  
  
  // --- BEGIN step finder (maneuver-anchored) ---
  if (leg._stepsResolved && leg._stepsResolved.length > 0) {
    // progress along leg (you already computed traveledDistance)
    
    let prog_m = Math.max(0, Math.min(traveledDistance || 0, legLen));

    // light smoothing: weaker in manual mode so turns don't skip
    if (!window.__navProgS) window.__navProgS = { prev: null };
    const prevS = window.__navProgS.prev;
    const alpha = isManualMode.value ? 0.25 : 0.6;
    prog_m = (prevS == null) ? prog_m : (alpha * prog_m + (1 - alpha) * prevS);
    window.__navProgS.prev = prog_m;

    const steps = leg._stepsResolved;

    // tolerances
    const speedMps = (leg.duration_s && leg.distance_m > 0) ? (leg.distance_m / leg.duration_s) : 1.35;
    const LOOKAHEAD_MAX = 100;   // don't announce farther than this
    const UPCOMING_EPS  = Math.max(12, speedMps * 2.0);
    const PASSED_EPS    = 4;     // after ~4 m past the start, skip (no lingering)
    const EPS_R         = 0.02;  // small ratio fallback

    const prog_r = legLen > 0 ? (prog_m / legLen) : 0;

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      const stepStart = Number(step._start_m) || 0;
      const delta     = stepStart - prog_m;   // + ahead, - behind
      const passedBy  = -delta;

      if (delta > LOOKAHEAD_MAX) continue;         // too far ahead
      if (passedBy > PASSED_EPS) continue;         // clearly passed

      // allow a bit beyond UPCOMING_EPS if ratios agree (geometry drift)
      const ratioOk = (legLen > 0) && ((stepStart / legLen) >= (prog_r - EPS_R));
      if (delta > UPCOMING_EPS && !ratioOk) continue;
      // NOW IT ACTUALLY WORKS QUITE OK:
      // significance filter (same as you had)
      const { type: maneuver, modifier } = parseManeuver(step);
      const mStr = `${maneuver}:${modifier}`; // for the 'sharp/slight' checks you already do

      const hasLeft  = modifier.includes('left')  || mStr.includes('left');
      const hasRight = modifier.includes('right') || mStr.includes('right');
      const hasUturn = /u[- ]?turn/.test(modifier) || mStr.includes('uturn');
      const signif = new Set([
        'turn','fork','merge','ramp','on ramp','off ramp',
        'roundabout','rotary','exit roundabout','end of road',
        'continue','new name'
      ]);
      if (!(signif.has(maneuver) || hasLeft || hasRight || hasUturn)) continue;

      // map direction (your existing mapping)
      let turnDirection = 'Turn';
      if (hasUturn) turnDirection = 'Make U-turn';
      else if (maneuver.includes('roundabout') || maneuver === 'rotary') turnDirection = 'Enter roundabout';
      else if (maneuver.includes('ramp')) turnDirection = 'Take ramp';
      else if (maneuver === 'merge') turnDirection = 'Merge';
      else if (maneuver === 'fork') {
        if (hasLeft && !hasRight) turnDirection = 'Keep left';
        else if (hasRight && !hasLeft) turnDirection = 'Keep right';
        else turnDirection = 'Keep straight';
      } else if (hasLeft && !hasRight) {
        if (modifier.includes('sharp') || mStr.includes('sharp')) turnDirection = 'Sharp left';
        else if (modifier.includes('slight') || mStr.includes('slight')) turnDirection = 'Slight left';
        else turnDirection = 'Turn left';
      } else if (hasRight && !hasLeft) {
        if (modifier.includes('sharp') || mStr.includes('sharp')) turnDirection = 'Sharp right';
        else if (modifier.includes('slight') || mStr.includes('slight')) turnDirection = 'Slight right';
        else turnDirection = 'Turn right';
      }

      const distToTurn = Math.max(0, Math.round(Math.max(0, delta)));
      nextTurn = {
        direction: turnDirection,
        distance_m: distToTurn,
        time_s: Math.round(distToTurn / (speedMps || 1.35)),
      };
      break;
    }
  }
  // --- END step finder ---
  
  // Calculate time to next stop
  // Prefer OSRM's actual walking time (accounts for route complexity, elevation, etc.)
  // Fall back to distance/speed estimate if OSRM data not available
  let timeToNextStop;
  
  if (leg.duration_s && legLen > 0) {
    // Use OSRM's actual walking time, proportional to remaining distance
    const progressRatio = 1 - (remainingDistance / legLen);
    const elapsedTime = leg.duration_s * Math.max(0, Math.min(1, progressRatio));
    timeToNextStop = Math.round(Math.max(0, leg.duration_s - elapsedTime));
  } else {
    // Fallback: fixed walking speed (1.35 m/s = ~4.86 km/h)
    const walkingSpeedMps = 1.35;
    timeToNextStop = Math.round(remainingDistance / walkingSpeedMps);
  }
  
  // Add time to next turn if we have turn info
  if (nextTurn && nextTurn.distance_m) {
    // Use OSRM's average speed for the leg (more accurate than fixed speed)
    if (leg.duration_s && leg.distance_m && leg.distance_m > 0) {
      const avgSpeedMps = leg.distance_m / leg.duration_s;
      nextTurn.time_s = Math.round(nextTurn.distance_m / avgSpeedMps);
    } else {
      // Fallback: fixed walking speed (1.35 m/s = ~4.86 km/h)
      const walkingSpeedMps = 1.35;
      nextTurn.time_s = Math.round(nextTurn.distance_m / walkingSpeedMps);
    }
  }
  
  return {
    legIndex: legIndex, // Include leg index for highlighting
    distance_m: Math.max(0, Math.round(remainingDistance)),
    next_street_name: leg.next_street_name || 'Continue straight',
    nextStopName,
    duration_s: leg.duration_s,
    time_s: timeToNextStop, // Time in seconds to reach next stop
    nextTurn: nextTurn, // Turn information
    deviationFromRoute: Math.round(deviationFromRoute), // Distance in meters from route path
    isOffRoute: deviationFromRoute > DEVIATION_THRESHOLD, // True if significantly off-route
    nearestRoutePoint: nearestRoutePoint, // [lat, lon] of nearest point on route (for visual indicator)

    onPath: deviationFromRoute <= PATH_TOL,
    traveledDistance_m: Math.max(0, Math.round(traveledDistance)),
    legDistance_m: Math.max(0, Math.round(leg.distance_m || 0)),
  };
});

function formatDistance(meters) {
  if (meters === null || meters === undefined || isNaN(meters)) return '';
  // Always show at least "0 m" if we have a valid number (including 0)
  if (meters < 1000) {
    return `${Math.round(meters)} m`;
  }
  return `${(meters / 1000).toFixed(1)} km`;
}

function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '';
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (minutes < 60) {
    return secs > 0 ? `${minutes}m ${secs}s` : `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

/* ---------------- bottom sheet ---------------- */
const STATES = ["peek", "mid", "expanded"];
//const STATE_POS = { peek: 88, mid: 42, expanded: 0 };

const STATE_POS_MAP = {
  planning: { peek: 88, mid: 1,  expanded: 0 },  
  poi:      { peek: 88, mid: 42, expanded: 0 },  
};

// Which set is active now?
const activeStatePos = computed(() =>
  selectedPoi.value ? STATE_POS_MAP.poi : STATE_POS_MAP.planning
);

const sheetState = ref("mid");
const STEP_TRIGGER_PX = 28;

const dragging = ref(false);
let dragStartY = 0, lastY = 0;
let dragStartTranslate = activeStatePos.value[sheetState.value];
let dragTranslate      = activeStatePos.value[sheetState.value];

const sheetStyle = computed(() => ({
  transform: `translateY(${dragging.value ? dragTranslate : activeStatePos.value[sheetState.value]}%)`,
}));

function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

function getY(evt) {
  if (evt.touches && evt.touches.length) return -evt.touches[0].clientY;
  if (evt.changedTouches && evt.changedTouches.length) return -evt.changedTouches[0].clientY;
  return -evt.clientY;
}
function onPointerDown(e) {
  e.preventDefault?.();
  dragging.value = true;
  dragStartY = getY(e);
  lastY = dragStartY;
  dragStartTranslate = activeStatePos.value[sheetState.value];
  dragTranslate = dragStartTranslate;
  window.addEventListener("pointermove", onPointerMove, { passive: false });
  window.addEventListener("pointerup", onPointerUp, { passive: false });
  window.addEventListener("touchmove", onPointerMove, { passive: false });
  window.addEventListener("touchend", onPointerUp, { passive: false });
 
}
function onPointerMove(e) {
  e.preventDefault?.();
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

  //emulate Read more / Show less when a POI is open
  /* if (selectedPoi.value && shouldClamp.value) {
    showFullExtract.value = (target === 'expanded'); // expanded => read more; else show less
  } */
  // Always sync with sheet state when inspecting a POI
  if (selectedPoi.value) {
    showFullExtract.value = (target === 'expanded'); // expanded => full; mid/peek => compact
  }

  sheetState.value = target;
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  window.removeEventListener("touchmove", onPointerMove);
  window.removeEventListener("touchend", onPointerUp);
}

//--------------------HELPERS FOR OPENING POI IN BOTTOM SHEET--------------------------
function openPoiInSheet(props) {
  const det = props?.det || props?.details || {};
  const wv = props?.wv || props?.wiki || null;
  const kindsArr = Array.isArray(props?.kinds)
    ? props.kinds
    : typeof props?.kinds === "string"
    ? props.kinds.split(",").map((s) => s.trim())
    : [];

  const extractFull = det?.wikipedia_extracts?.text || "";
  const xid = props?.xid;
  const otm =
    det?.otm ||
    det?.url ||
    (xid ? `https://opentripmap.com/en/card?xid=${encodeURIComponent(xid)}` : null);

  const devScore = props?.score ?? (det?.score ?? null);

  selectedPoi.value = {
    ...props,
    kindsArr,
    wv,
    extractFull,
    otm,
    devScore,
  };

  showFullExtract.value = false;
  sheetState.value = 'mid';

  if (props.lat && props.lon) {
    const z = map?.getZoom?.() ?? 0;
    if (z < 17) {
      map.setView([props.lat, props.lon], 17);
    } else {
      map.panTo([props.lat, props.lon]); // keep current zoom, no zoom-out
    }
  }
  //if (props.lat && props.lon) map.setView([props.lat, props.lon], 17);


}

function clearSelectedPoi() {
  selectedPoi.value = null;
  showFullExtract.value = false;

  if (currentSelectedMarker) {
    currentSelectedMarker.getElement()?.classList.remove('pulse');
    const p = currentSelectedMarker.options.props;
    const hasWiki = !!((p?.wv || p?.wiki)?.title);
    const inRoute = isPoiInActiveRoute(p);
    currentSelectedMarker.setIcon(inRoute ? poiInRouteIcon : (hasWiki ? poiGreenIcon : poiGrayIcon));
    currentSelectedMarker = null;
  }
  //sheetState.value = "mid";
}

async function addPoiToRoute(poi) {
  // plug in your real logic later
  toast(`Added "${poi.name || 'POI'}" to route`);
  await loadPois();
}

async function removePoiFromRoute(poi) {
  // plug in your real logic later
  toast(`Removed "${poi.name || 'POI'}" from route`);
  await loadPois();
}

function onToggleReadMore() {
  showFullExtract.value = !showFullExtract.value;
  if (showFullExtract.value) {
    // expand to full height when showing all text
    sheetState.value = 'expanded';
  } else {
    // collapse back to normal view when hiding it again
    sheetState.value = 'mid';
  }


}


/* ---------------- Mode Toggle ---------------- */
function toggleMode() {
  selectedPoi.value = null;
  isRoutePlanningMode.value = !isRoutePlanningMode.value;
  if (isRoutePlanningMode.value && confirmedRoute.value) {
    // When switching back to planning mode, keep the route displayed but allow modifications
    displayRoute(confirmedRoute.value);
    selectedEndStart.value = false;  //From oliver
    stopNavigationTracking();
    currentNavLegIndex.value = 0;
    currentPoiIndex.value = Math.min(1, (confirmedRoute.value.stops?.length || 1) - 1);
    navMode.value = 'navigating';
    //zoomToCurrentPoi();
    startNavigationTracking();
  } else if (confirmedRoute.value) {
    // When switching to navigation mode, focus on current POI
    zoomToCurrentPoi();
    startNavigationTracking();
  }
}

function cancelNavigation() {
  // fully clear route layers, markers, navigation, and reactive state
  resetPlanningState();
  toast("🛑 Navigation cancelled. You’re back in planning mode.");
}

function goBackToPlanning() {
  resetPlanningState();   // fully clears old route & UI and returns to planning
  toast("🔄 Start planning a new route");
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

/* ---------------- use my location ---------------- */
function useMyLocation() {
  if (!navigator.geolocation) {
    toast("Geolocation not supported");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      lat.value = coords.latitude;
      lon.value = coords.longitude;
      const p = [lat.value, lon.value];

      if (origin) origin.setLatLng(p);
      if (circle) circle.setLatLng(p);
      if (map) map.setView(p, Math.max(map.getZoom?.() || 14, 15));

      loadPois();
      toast("📡 Positioned to your location");
    },
    (err) => {
      console.warn("Geolocation error:", err);
      toast("Unable to get location");
    },
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 10000 }
  );
}

/* ---------------- marker icons ---------------- */
const startIcon = L.icon({
  iconUrl: new URL("/src/icons/StartMarker.png", import.meta.url).href,
  iconSize: [40, 40],
});

const currentLocationIcon = L.icon({
  iconUrl: new URL("/src/icons/StartMarkerOld.png", import.meta.url).href,
  iconSize: [34, 34],
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

const poiSelectedIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [26, 40],
  iconAnchor: [13, 40],
  shadowSize: [41, 41],
});

const poiInRouteIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [22, 34],
  iconAnchor: [11, 34],
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

function setAsStart(newLat, newLon) {
  // Update the reactive values that are used for route generation
  lat.value = newLat;
  lon.value = newLon;
  
  // Update the start position markers
  origin.setLatLng([newLat, newLon]);
  circle.setLatLng([newLat, newLon]);
  
  // Show feedback
  toast("✅ Start position updated!");
  
  // Close any open popups
  //map.closePopup();
  
  // Reload POIs around the new start position
  loadPois();
}

function setAsEnd(newLat, newLon) {
  if (tripMode.value !== "end") {
    tripMode.value = "end";
  }
  
  // Set end position (the reactive values used for route generation)
  endLat.value = newLat;
  endLon.value = newLon;
  endPositionSelected.value = true;
  
  // Update or create end marker on the map
  if (endMarker) endMarker.remove();
  endMarker = L.marker([endLat.value, endLon.value], { icon: endIcon }).addTo(map);
  
  // Show feedback
  toast("✅ End position set! You can now generate your route.");
  
  // Close any open popups
  //map.closePopup();
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
  // If a POI sheet is open, close it and return
  if (selectedPoi.value) {
    clearSelectedPoi();
    return;
  }

  // Don't show coordinate popup during route selection
  if (selectedEndStart.value) return;

  // Don't show coordinate popup during navigation mode
  if (!isRoutePlanningMode.value) return;

  const { lat: clat, lng: clng } = e.latlng;
  const popupContent = buildPoiPopup({ lat: clat, lon: clng }, true);
  L.popup().setLatLng(e.latlng).setContent(popupContent).openOn(map);
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
  //const { data } = await api.post("/pois", payload);

  if (poiCluster) poiCluster.remove();
  poiCluster = L.markerClusterGroup({
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
  });

  (data.features || []).forEach((f) => {
    const [gLon, gLat] = f.geometry.coordinates;
    const rawProps = f.properties || {};

    // Ensure the props we keep on the marker include lat/lon/geometry for matching
    const baseProps = { ...rawProps, lat: gLat, lon: gLon, geometry: f.geometry };

    // Pick icon based on route membership first, then wiki/gray
    const hasWiki  = !!((baseProps.wv || baseProps.wiki)?.title);
    const inRoute  = isPoiInActiveRoute(baseProps);
    const icon     = inRoute ? poiInRouteIcon : (hasWiki ? poiGreenIcon : poiGrayIcon);

    const marker = L.marker([gLat, gLon], { icon });
    marker.options.props = baseProps; // keep for later comparisons

    marker.on('click', () => {
      // unhighlight previous
      if (currentSelectedMarker) {
        currentSelectedMarker.getElement()?.classList.remove('pulse');
        const prevProps   = currentSelectedMarker.options.props;
        const prevHasWiki = !!((prevProps?.wv || prevProps?.wiki)?.title);
        const prevInRoute = isPoiInActiveRoute(prevProps);
        currentSelectedMarker.setIcon(prevInRoute ? poiInRouteIcon : (prevHasWiki ? poiGreenIcon : poiGrayIcon));
      }

      // highlight this one
      marker.setIcon(poiSelectedIcon);
      // ensure the DOM element exists before adding the class
      requestAnimationFrame(() => marker.getElement()?.classList.add('pulse'));

      currentSelectedMarker = marker;

      openPoiInSheet(baseProps);
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
  navMode.value = 'navigating';
  visitedIdx.value = new Set();
  currentPoiIndex.value = Math.min(1, (confirmedRoute.value?.stops?.length || 1) - 1);
  currentNavLegIndex.value = 0; // leg 0 = start -> stop 1

  selectedPoi.value = null; 
  confirmedRoute.value = generatedRoutes.value[currentRouteIndex.value];
  currentPoiIndex.value = Math.min(1, (confirmedRoute.value?.stops?.length || 1) - 1);
  currentNavLegIndex.value = 0; // Reset navigation leg index to start with first leg
  isRoutePlanningMode.value = false;
  selectedEndStart.value = false; // THIS ONE, OLIVER WANTED TO REMOVE, NOT SURE WHY
  updateRoutePoiMarkers();
  sheetState.value = "mid";
  
  // Start navigation from the route's start position (which may be manually selected)
  // This respects the user's manually selected start position instead of always using GPS
  const firstStop = confirmedRoute.value?.stops?.[0];
  if (firstStop) {
    // Use the route's start position (matches lat.value and lon.value used to generate route)
    const startPos = [firstStop.lat, firstStop.lon];
    currentGPSPosition.value = startPos;
    
    // Create the current location marker at the start position
    if (!currentLocationMarker) {
      currentLocationMarker = L.marker(startPos, { 
        icon: currentLocationIcon, 
        zIndexOffset: 1000,
        draggable: true
      }).addTo(map);
      
      // Set up drag handlers
      currentLocationMarker.on('dragstart', () => {
        isManualMode.value = true;
      });
      
      currentLocationMarker.on('drag', (e) => {
        const pos = e.target.getLatLng();
        currentGPSPosition.value = [pos.lat, pos.lng];
        if (!isRoutePlanningMode.value && map) {
          const z = map.getZoom?.() || 0;
          if (z < 17) map.setView(pos, 17); else map.panTo(pos);
        }
      });
      
      currentLocationMarker.on('dragend', (e) => {
        const pos = e.target.getLatLng();
        currentGPSPosition.value = [pos.lat, pos.lng];
        if (!isRoutePlanningMode.value && map) {
          map.panTo(pos);
        }
        evaluateArrival();
      });
    } else {
      currentLocationMarker.setLatLng(startPos);
    }
    
    // Center map on the start position
    if (map) map.setView(startPos, 17);
    
    // Start in manual mode to preserve the manually set start position
    // GPS tracking will start but won't override until user clicks "Reset to GPS"
    isManualMode.value = true;
  }
  
  // Start GPS tracking (but it won't update position while in manual mode)
  // User must click "Reset to GPS" to enable GPS tracking
  startNavigationTracking();

  updateRoutePoiMarkers();
  sheetState.value = "mid";
  loadPois();
}

function prevPoi() {
  if (currentPoiIndex.value > 0) {
    currentPoiIndex.value--;
    // updateRoutePoiMarkers() and zoomToCurrentPoi() are handled by the watcher
    poiIndexChangeReason.value = 'manual';
  }
}

function nextPoi() {
  if (confirmedRoute.value && currentPoiIndex.value < confirmedRoute.value.stops.length - 1) {
    currentPoiIndex.value++;
    // updateRoutePoiMarkers() and zoomToCurrentPoi() are handled by the watcher
    poiIndexChangeReason.value = 'manual';
  }
}

/* function zoomToCurrentPoi() {
  if (!confirmedRoute.value || !confirmedRoute.value.stops || confirmedRoute.value.stops.length === 0) return;
  
  const stop = confirmedRoute.value.stops[currentPoiIndex.value];
  map.setView([stop.lat, stop.lon], 17);
} */
function zoomToCurrentPoi() {
  if (!confirmedRoute.value || !confirmedRoute.value.stops || confirmedRoute.value.stops.length === 0) return;
  const stop = confirmedRoute.value.stops[currentPoiIndex.value];
  const z = map?.getZoom?.() ?? 0;
  if (z < 17) {
    map.setView([stop.lat, stop.lon], 17);
  } else {
    map.panTo([stop.lat, stop.lon]);
  }
}

function updateRoutePoiMarkers() {
  // Clear existing route POI markers
  routePoiMarkers.forEach(marker => marker.remove());
  routePoiMarkers = [];

  if (!confirmedRoute.value || !confirmedRoute.value.stops) return;

  // Hide origin marker when in navigation mode
  if (origin) {
    if (!isRoutePlanningMode.value) {
      origin.setOpacity(0);
      origin.dragging?.disable();
    } else {
      origin.setOpacity(1);
      origin.dragging?.enable();
    }
  }

  // Add route POIs with special styling
  confirmedRoute.value.stops.forEach((stop, index) => {
    let icon;
    if (index === 0) {
      // Skip start marker if in navigation mode (GPS marker replaces it)
      if (!isRoutePlanningMode.value) return;
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

function isPoiInActiveRoute(poi) {
  const r = activeRoute.value;                // <- use candidate when selecting, confirmed when navigating
  if (!r?.stops?.length) return false;

  // Prefer stable IDs
  const xid = poi?.xid ?? poi?.id ?? poi?.otm_id;
  if (xid) return r.stops.some(s => s.xid === xid || s.id === xid || s.otm_id === xid);

  // Fallback: location (and optional name assist)
  const plat = Number(poi?.lat ?? poi?.geometry?.coordinates?.[1]);
  const plon = Number(poi?.lon ?? poi?.geometry?.coordinates?.[0]);
  if (!Number.isFinite(plat) || !Number.isFinite(plon)) return false;

  const NAME = (poi?.name || '').trim().toLowerCase();
  const TOL  = 50; // meters – real OSM/OTM coords often differ by >12 m

  return r.stops.some(s => {
    const d = haversineDistance(plat, plon, Number(s.lat), Number(s.lon));
    if (d <= TOL) return true;
    // If names match, allow a looser position tolerance
    if (NAME && s.name && s.name.trim().toLowerCase() === NAME) {
      return d <= 150;
    }
    return false;
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
    //const { data } = await api.post("/tour", payload);

    // Map backend route POIs to stops (start, poi..., [end]) with real details
    const routePois = Array.isArray(data.route_pois) ? data.route_pois : [];
    const stopsWithDetails = (data.stops || []).map((s, idx, arr) => {
      const isStart = idx === 0;
      const isEnd = idx === arr.length - 1 && tripMode.value === "end" && !!arr.length;
      if (isStart || isEnd) {
        return {
          ...s,
          name: s.name || (isStart ? "Start" : "End"),
        };
      }
      const rp = routePois[idx - 1] || {};
      const kindsArr = Array.isArray(rp.kinds)
        ? rp.kinds
        : typeof rp.kinds === 'string'
          ? rp.kinds.split(',').map(t => t.trim()).filter(Boolean)
          : [];
      const description = rp?.det?.wikipedia_extracts?.text || '';
      return {
        ...s,
        name: rp.name || s.name || `POI ${idx}`,
        categories: kindsArr,
        description,
        det: rp.det,
        wv: rp.wv,
        xid: rp.xid,
      };
    });

    // Keep multi-candidate UI but use real enriched stops
    generatedRoutes.value = Array(5).fill(null).map((_, index) => ({
      ...data,
      id: index,
      distance: (Math.random() * 5 + 2).toFixed(1),
      time: `${Math.floor(Math.random() * 120 + 30)} min`,
      stops: stopsWithDetails,
    }));
    
    currentRouteIndex.value = 0;
    confirmedRoute.value = null;
    isRoutePlanningMode.value = true;
    
    displayRoute(generatedRoutes.value[0]);
    sheetState.value = "mid";
    selectedEndStart.value = true;
    await loadPois();
  } catch (err) {
    console.error("Failed to build tour:", err);
  }
}

function displayRoute(routeData) {
  if (tourLayer) tourLayer.remove();
  if (currentLegLayer) {
    // Clear pulse interval if exists
    if (currentLegLayer._pulseInterval) {
      clearInterval(currentLegLayer._pulseInterval);
    }
    currentLegLayer.remove();
    currentLegLayer = null;
  }
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
  
  // Update current leg highlight after route is displayed
  if (!isRoutePlanningMode.value && currentNavInfo.value) {
    updateCurrentLegHighlight(currentNavInfo.value);
  }
}

function clearRouteDisplay() {
  // main route layer
  if (tourLayer) { try { tourLayer.remove(); } catch {} tourLayer = null; }

  // highlighted leg (with pulsing)
  if (currentLegLayer) {
    if (currentLegLayer._pulseInterval) {
      clearInterval(currentLegLayer._pulseInterval);
      currentLegLayer._pulseInterval = null;
    }
    try { currentLegLayer.remove(); } catch {}
    currentLegLayer = null;
  }

  // deviation line
  if (deviationLineLayer) { try { deviationLineLayer.remove(); } catch {} deviationLineLayer = null; }

  // any stop markers rendered for the route
  (window._stopMarkers || []).forEach(m => { try { m.remove(); } catch {} });
  window._stopMarkers = [];

  // special route POI markers
  routePoiMarkers.forEach(m => { try { m.remove(); } catch {} });
  routePoiMarkers = [];
}

function resetPlanningState() {
  // map layers
  clearRouteDisplay();
  navMode.value = 'navigating';
  visitedIdx.value = new Set();

  // navigation tracking + simulated GPS marker
  stopNavigationTracking();
  if (currentLocationMarker) { try { currentLocationMarker.remove(); } catch {} currentLocationMarker = null; }

  // reactive route state
  confirmedRoute.value    = null;
  generatedRoutes.value   = [];
  currentRouteIndex.value = 0;
  currentPoiIndex.value   = 0;
  currentNavLegIndex.value = 0;

  // end position state
  endPositionSelected.value = false;
  endLat.value = null;
  endLon.value = null;
  if (endMarker) { try { endMarker.remove(); } catch {} endMarker = null; }

  // UI mode
  isRoutePlanningMode.value = true;
  selectedEndStart.value    = false;  // back to the “Plan” view
  selectedPoi.value         = null;
  sheetState.value          = "mid";

  // restore draggable origin marker
  if (origin) { origin.setOpacity(1); origin.dragging?.enable(); }

  // refresh POIs around current start/radius
  loadPois();
}

/* ---------------- generate ---------------- */
async function generateRoute() {
  if (isGenerating.value) return;
  selectedPoi.value = null;
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
    if (currentLegLayer) {
      if (currentLegLayer._pulseInterval) {
        clearInterval(currentLegLayer._pulseInterval);
      }
      currentLegLayer.remove();
      currentLegLayer = null;
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
  map.on("dragstart", clearSelectedPoi);
  map.on("zoomstart", clearSelectedPoi);

  // Try to use browser geolocation on load
  useMyLocation();
});

onBeforeUnmount(() => {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", onPointerUp);
  window.removeEventListener("touchmove", onPointerMove);
  window.removeEventListener("touchend", onPointerUp);
  stopNavigationTracking();
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

watch(selectedPoi, () => {
  dragStartTranslate = activeStatePos.value[sheetState.value];
  dragTranslate      = dragStartTranslate;
});

watch([selectedPoi, sheetState], () => {
  dragStartTranslate = activeStatePos.value[sheetState.value];
  dragTranslate      = dragStartTranslate;
});

// Watch for changes in current navigation leg and update highlighted path
watch(currentNavInfo, (navInfo) => {
  updateCurrentLegHighlight(navInfo);
  updateDeviationLine(navInfo);
}, { immediate: true });

// Watch GPS position and advance leg index when user reaches destination stop
/* watch(currentGPSPosition, (pos) => {
  if (!pos || !confirmedRoute.value || isRoutePlanningMode.value) return;

  const navInfo = currentNavInfo.value;
  if (!navInfo) return;

  const now = Date.now() / 1000;
  const { onPath, traveledDistance_m, legDistance_m } = navInfo;

  // meters remaining ALONG the path to the current leg's destination
  const alongLeft = Math.max(0, (legDistance_m || 0) - (traveledDistance_m || 0));

  if (onPath && alongLeft <= ARRIVAL_RADIUS) {
    // inside arrival zone while on the route – start/continue debounce window
    if (!arrivalCandidateStartedAt.value) arrivalCandidateStartedAt.value = now;
    const elapsed = now - arrivalCandidateStartedAt.value;

    if (elapsed >= ARRIVAL_DEBOUNCE_S) {
      // ✅ arrived: advance leg/poi if possible

      const legs = confirmedRoute.value.navigation_legs || [];
      if (currentNavLegIndex.value < legs.length - 1) {
        poiIndexChangeReason.value = 'auto';
        currentNavLegIndex.value += 1;
        currentPoiIndex.value = Math.min(
          currentPoiIndex.value + 1,
          (confirmedRoute.value.stops?.length || 1) - 1
        );
      } else {
        // last leg finished; you could show a “Route complete” toast/banner here
        toast("🎉 Route complete!");
      }
      arrivalCandidateStartedAt.value = null;
    }
  } else {
    // left the arrival zone or off-path → reset debounce
    arrivalCandidateStartedAt.value = null;
  }
}); */

//watch(currentGPSPosition, evaluateArrival);

watch(currentGPSPosition, () => {
  // tick both arrival debounce and depart probe on any position update
  maybeAutoDepartFromArrived();
  evaluateArrival();
});

// Watch for changes in currentPoiIndex and automatically zoom/pan to that stop
// This works both when manually switching stops AND when automatically arriving at a stop
watch(currentPoiIndex, (newIndex, oldIndex) => {
  if (!confirmedRoute.value || !map) return;
  
  // Only auto-zoom if we're in navigation mode (not planning mode)
  // In planning mode, user might be exploring, so don't force zoom
  if (isRoutePlanningMode.value) {
    // In planning mode, just update markers
    updateRoutePoiMarkers();
  } else {
    // In navigation mode, update markers and zoom/pan to the stop
    updateRoutePoiMarkers();
    //zoomToCurrentPoi();
    
    const isManualJump = poiIndexChangeReason.value === 'manual';
    // If manually switching stops (not auto-arrival), move the GPS marker to simulate position
    // Only do this if the index actually changed (avoid on initial mount)
    if (
      teleportOnManualJump.value &&
      oldIndex !== undefined && oldIndex !== null &&
      newIndex !== oldIndex &&
      currentLocationMarker &&
      isManualJump
    ) {
      const stop = confirmedRoute.value.stops[newIndex];
      if (stop) {
        isManualMode.value = true;
        const newPos = [stop.lat, stop.lon];
        currentLocationMarker.setLatLng(newPos);
        currentGPSPosition.value = newPos;
        if (newIndex > 0) {
          currentNavLegIndex.value = newIndex - 1;
        } else {
          currentNavLegIndex.value = 0;
        }
      }
    }
  }
  poiIndexChangeReason.value = 'auto';
}, { immediate: false });



function evaluateArrival() {
  if (!confirmedRoute.value || isRoutePlanningMode.value) return;
  if (navMode.value === 'arrived') return; // ← prevent re-firing while parked at a stop

  const navInfo = currentNavInfo.value;
  if (!navInfo) return;

  const now = Date.now() / 1000;
  const { onPath, traveledDistance_m, legDistance_m } = navInfo;
  const alongLeft = Math.max(0, (legDistance_m || 0) - (traveledDistance_m || 0));

  if (onPath && alongLeft <= ARRIVAL_RADIUS) {
    if (!arrivalCandidateStartedAt.value) arrivalCandidateStartedAt.value = now;
    const elapsed = now - arrivalCandidateStartedAt.value;
    if (elapsed >= ARRIVAL_DEBOUNCE_S) {
      // Destination of the current leg
      const destIdx = Math.min(
        (currentNavLegIndex.value + 1),
        (confirmedRoute.value.stops?.length || 1) - 1
      );
      currentPoiIndex.value = destIdx;   // <- show the place we actually arrived at
      markArrived(false);                // sets navMode='arrived' + visited
      arrivalCandidateStartedAt.value = null;
    }
  } else {
    arrivalCandidateStartedAt.value = null;
  }
}

function updateCurrentLegHighlight(navInfo) {
  // Remove existing highlight
  if (currentLegLayer) {
    // Clear pulse interval if exists
    if (currentLegLayer._pulseInterval) {
      clearInterval(currentLegLayer._pulseInterval);
      currentLegLayer._pulseInterval = null;
    }
    currentLegLayer.remove();
    currentLegLayer = null;
  }
  
  // Only show highlight during navigation mode
  if (!navInfo || isRoutePlanningMode.value || !confirmedRoute.value || !map) return;
  
  const navLegs = confirmedRoute.value.navigation_legs || [];
  const leg = navLegs[navInfo.legIndex];
  
  if (!leg || !leg.coords_latlon || leg.coords_latlon.length === 0) return;
  
  // Convert [lat, lon] to [lon, lat] for GeoJSON
  const coordsLonLat = leg.coords_latlon.map(([lat, lon]) => [lon, lat]);
  
  // Create highlighted path with distinctive styling
  currentLegLayer = L.geoJSON({
    type: "Feature",
    geometry: {
      type: "LineString",
      coordinates: coordsLonLat
    }
  }, {
    style: {
      color: "#00ff00", // Bright green
      weight: 6, // Thicker than the main route
      opacity: 0.9,
      lineCap: "round",
      lineJoin: "round",
      dashArray: "10, 5" // Dashed pattern for visibility
    }
  }).addTo(map);
  
  // Add a pulsing effect by toggling dash pattern
  if (currentLegLayer) {
    let dashToggle = true;
    const pulseInterval = setInterval(() => {
      if (!currentLegLayer || !map.hasLayer(currentLegLayer)) {
        clearInterval(pulseInterval);
        return;
      }
      dashToggle = !dashToggle;
      currentLegLayer.setStyle({
        dashArray: dashToggle ? "10, 5" : "20, 10"
      });
    }, 1000);
    
    // Store interval ID to clear it later
    if (currentLegLayer) {
      currentLegLayer._pulseInterval = pulseInterval;
    }
  }
}

function updateDeviationLine(navInfo) {
  if (!navInfo || !map || !currentGPSPosition.value) return;
  
  // Remove existing deviation line
  if (deviationLineLayer) {
    deviationLineLayer.remove();
    deviationLineLayer = null;
  }
  
  // Only show deviation line if off-route and we have a nearest route point
  if (navInfo.isOffRoute && navInfo.nearestRoutePoint) {
    const [userLat, userLon] = currentGPSPosition.value;
    const [routeLat, routeLon] = navInfo.nearestRoutePoint;
    
    // Draw a line from user position to nearest route point
    deviationLineLayer = L.polyline(
      [[userLat, userLon], [routeLat, routeLon]],
      {
        color: '#ff6b00', // Orange-red color for deviation
        weight: 3,
        opacity: 0.7,
        dashArray: '5, 10', // Dashed line
        lineCap: 'round',
        lineJoin: 'round'
      }
    ).addTo(map);
  }
}

/* ---------------- navigation tracking ---------------- */
/**
 * GPS Location Explanation:
 * 
 * We use the browser's Geolocation API (navigator.geolocation) which:
 * 1. Uses device GPS, Wi-Fi positioning, and cell tower triangulation
 * 2. Is FREE (no API costs) - uses browser's built-in location services
 * 3. Requires user permission on first use
 * 
 * watchPosition() continuously updates the user's location:
 * - enableHighAccuracy: true = requests GPS (more accurate but uses more battery)
 * - maximumAge: 5000ms = allows cached location up to 5 seconds old
 * - timeout: 10000ms = gives GPS 10 seconds to respond before timing out
 * 
 * The location updates trigger:
 * - Marker position on map
 * - Map centering/following
 * - Navigation calculations (which leg you're on, distance to turns)
 * - Turn-by-turn instructions
 */
function startNavigationTracking() {
  if (!navigator.geolocation) return;
  if (geoWatchId !== null) return;
  geoWatchId = navigator.geolocation.watchPosition(
    ({ coords }) => {
      // Don't update if user is manually dragging

      
      const p = [coords.latitude, coords.longitude];
      currentGPSPosition.value = p; // Update GPS position for navigation calculations
      maybeAutoDepartFromArrived();
      if (isManualMode.value) return;

      if (!currentLocationMarker) {
        currentLocationMarker = L.marker(p, { 
          icon: currentLocationIcon, 
          zIndexOffset: 1000,
          draggable: true // Make marker draggable for simulation
        }).addTo(map);
        
        // Set up drag handlers
        currentLocationMarker.on('dragstart', () => {
          isManualMode.value = true; // Pause GPS updates while dragging
        });
        
        let followTimeout = null;
        currentLocationMarker.on('drag', (e) => {
          const pos = e.target.getLatLng();
          currentGPSPosition.value = [pos.lat, pos.lng];
          clearTimeout(followTimeout);
          followTimeout = setTimeout(() => {
            if (!isRoutePlanningMode.value && map) {
              map.panTo(pos, { animate: true, duration: 0.2 });
            }
          }, 50);
        });
        
        currentLocationMarker.on('dragend', (e) => {
          const pos = e.target.getLatLng();
          currentGPSPosition.value = [pos.lat, pos.lng];
          if (!isRoutePlanningMode.value && map) {
            const z = map.getZoom?.() || 0;
            if (z < 17) map.setView(pos, 17);
            else map.panTo(pos);
          }
        });
      } else {
        currentLocationMarker.setLatLng(p);
      }
      if (!isRoutePlanningMode.value && map && !isManualMode.value) {
        const z = map.getZoom?.() || 0;
        if (z < 17) map.setView(p, 17); else map.panTo(p);
      }
    },
    (err) => {
      console.warn('watchPosition error', err);
    },
    { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
  );
}

function resetToGPSLocation() {
  if (!navigator.geolocation) {
    toast("Geolocation not supported");
    return;
  }
  
  // Show loading state
  isResettingGPS.value = true;
  
  // Exit manual mode and resume GPS tracking
  isManualMode.value = false;
  
  // Helper function to update marker position
  const updateMarkerPosition = (p) => {
    currentGPSPosition.value = p; // Update GPS position
    
    if (currentLocationMarker) {
      currentLocationMarker.setLatLng(p);
    } else {
      currentLocationMarker = L.marker(p, { 
        icon: currentLocationIcon, 
        zIndexOffset: 1000,
        draggable: true
      }).addTo(map);
      
      // Set up drag handlers
      currentLocationMarker.on('dragstart', () => {
        isManualMode.value = true;
      });
      
      currentLocationMarker.on('drag', (e) => {
        const pos = e.target.getLatLng();
        currentGPSPosition.value = [pos.lat, pos.lng]; // Update position for navigation
        if (!isRoutePlanningMode.value && map) {
          const z = map.getZoom?.() || 0;
          if (z < 17) map.setView(pos, 17); else map.panTo(pos);
        }
      });
      
      currentLocationMarker.on('dragend', (e) => {
        const pos = e.target.getLatLng();
        currentGPSPosition.value = [pos.lat, pos.lng]; // Update position for navigation
        if (!isRoutePlanningMode.value && map) {
          map.panTo(pos);
        }
      });
    }
    
    if (map) {
      const z = map.getZoom?.() || 0;
      if (z < 17) map.setView(p, 17); else map.panTo(p);
    }
    
    // Reset navigation state to start when resetting GPS
    if (confirmedRoute.value && !isRoutePlanningMode.value) {
      currentNavLegIndex.value = 0; // Reset to first navigation leg
      currentPoiIndex.value = 0; // Reset to first stop (start point)
      // The watcher will automatically update markers and zoom when currentPoiIndex changes
    }
    
    // Hide loading state
    isResettingGPS.value = false;
    toast("📍 Reset to GPS location");
  };
  
  // If we already have a current GPS position from watchPosition, use it as fallback
  const fallbackPosition = currentGPSPosition.value;
  
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      const p = [coords.latitude, coords.longitude];
      updateMarkerPosition(p);
    },
    (err) => {
      console.warn("Geolocation error:", err);
      
      // Provide specific error messages
      let errorMsg = "Unable to get GPS location";
      switch(err.code) {
        case err.PERMISSION_DENIED:
          errorMsg = "Location permission denied. Please enable location access in your browser settings.";
          break;
        case err.POSITION_UNAVAILABLE:
          errorMsg = "Location unavailable. Using last known position.";
          // Try to use fallback position if available
          if (fallbackPosition) {
            updateMarkerPosition(fallbackPosition);
            toast("📍 Using last known location");
            return;
          }
          break;
        case err.TIMEOUT:
          errorMsg = "Location request timed out. Using last known position.";
          // Try to use fallback position if available
          if (fallbackPosition) {
            updateMarkerPosition(fallbackPosition);
            toast("📍 Using last known location");
            return;
          }
          break;
        default:
          // For unknown errors, try fallback
          if (fallbackPosition) {
            updateMarkerPosition(fallbackPosition);
            toast("📍 Using last known location");
            return;
          }
      }
      
      isResettingGPS.value = false; // Hide loading state on error
      toast(errorMsg);
      isManualMode.value = false; // Allow GPS to resume if it was tracking
    },
    { 
      enableHighAccuracy: true, 
      timeout: 15000, // 15 seconds timeout
      maximumAge: 10000 // Allow using cached location up to 10 seconds old (faster response)
    }
  );
}

function stopNavigationTracking() {
  if (geoWatchId !== null && navigator.geolocation) {
    try { navigator.geolocation.clearWatch(geoWatchId); } catch {}
    geoWatchId = null;
  }
  if (currentLocationMarker) {
    try { currentLocationMarker.remove(); } catch {}
    currentLocationMarker = null;
  }
  isManualMode.value = false; // Reset manual mode flag
  
  // Remove current leg highlight when stopping navigation
  if (currentLegLayer) {
    if (currentLegLayer._pulseInterval) {
      clearInterval(currentLegLayer._pulseInterval);
    }
    currentLegLayer.remove();
    currentLegLayer = null;
  }
  
  // Remove deviation line when stopping navigation
  if (deviationLineLayer) {
    deviationLineLayer.remove();
    deviationLineLayer = null;
  }
}

const startAt = ref(new Date()); // or your preferred start time
if (!timeMin.value || timeMin.value <= 0) timeMin.value = 60; // default 1h

// Helpers
const pad2 = n => String(n).padStart(2,'0');
const hhmm = d => `${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
const addMin = (d,m) => new Date(d.getTime() + m * 60000);

const startTimeStr = computed(() => hhmm(startAt.value));

// Pretty duration output
const durationPretty = computed(() => {
  const m = Math.max(0, timeMin.value || 0);
  const h = Math.floor(m/60), r = m%60;
  if (h && r) return `${h}h ${r}m`;
  if (h) return `${h}h`;
  return `${r}m`;
});

// End time <-> duration
const endTimeStr = computed({
  get() {
    const end = addMin(startAt.value, timeMin.value || 0);
    return hhmm(end);
  },
  set(hhmmStr) {
    const [H, M] = (hhmmStr || '').split(':').map(n => parseInt(n, 10));
    if (Number.isFinite(H) && Number.isFinite(M)) {
      const end = new Date(startAt.value);
      end.setHours(H, M, 0, 0);
      if (end < startAt.value) end.setDate(end.getDate() + 1); // next day
      timeMin.value = Math.max(0, Math.round((end - startAt.value) / 60000));
    }
  }
});

</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  overscroll-behavior: none;
}

#map-container {
  position: relative;
  width: 100%;
  height: 100dvh;
  overflow: hidden;
}

#map {
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* Navigation Banner (Google Maps style) */
.nav-banner {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  background: rgba(15, 22, 32, 0.48);
  color: #eef4ff;
  backdrop-filter: blur(2px) saturate(115%);
  -webkit-backdrop-filter: blur(2px) saturate(115%);
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  border-bottom: 1px solid rgba(255,255,255,0.25);
  z-index: 1001;
  padding: 14px 18px;
  border-radius: 0 0 14px 14px;
}

.nav-banner-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Main Distance Display */
.nav-distance-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-distance {
  font-size: 1.8rem;
  font-weight: 800;
  color: #eef4ff;
  line-height: 1.1;
  letter-spacing: -0.5px;
}

.nav-distance.off-route-distance {
  color: #ff6b6b;
}

.nav-destination {
  font-size: 0.95rem;
  font-weight: 600;
  color: #eef4ff;
  line-height: 1.3;
  margin-top: 2px;
  opacity: 0.95;
}

.nav-time {
  font-size: 0.85rem;
  color: #eef4ff;
  font-weight: 500;
  margin-top: 2px;
  opacity: 0.85;
}

/* Turn Instruction (when close) - Primary Display */
.nav-turn-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(255,255,255,0.08);
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.25);
  border-left: 4px solid #6a5cff;
  margin-bottom: 4px;
}

.nav-turn-instruction-text {
  font-size: 1.2rem;
  font-weight: 700;
  color: #eef4ff;
  line-height: 1.4;
  letter-spacing: -0.3px;
}

.nav-turn-main .nav-turn-time {
  font-size: 0.85rem;
  color: #eef4ff;
  font-weight: 500;
  opacity: 0.85;
  margin-top: 2px;
}

/* "Then to destination" when turn is primary */
.nav-to-destination {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.9rem;
  color: #eef4ff;
  padding-left: 4px;
  margin-top: 4px;
  opacity: 0.9;
}

.nav-destination-label {
  font-weight: 500;
  opacity: 0.85;
  font-size: 0.85rem;
}

.nav-destination-distance {
  font-size: 1rem;
  opacity: 0.95;
  font-weight: 600;
  color: #eef4ff;
}

/* Upcoming Turn (secondary info) */
.nav-turn-upcoming {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 8px 12px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 6px;
  margin-top: 4px;
}

.nav-turn-upcoming .nav-turn-instruction-text {
  font-size: 0.9rem;
  font-weight: 600;
  color: #eef4ff;
  line-height: 1.3;
  opacity: 0.95;
}

.nav-turn-upcoming .nav-turn-time {
  font-size: 0.8rem;
  color: #eef4ff;
  font-weight: 500;
  opacity: 0.8;
}

/* Deviation Warning Styles */
.nav-deviation-warning {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 152, 0, 0.2);
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid rgba(255, 152, 0, 0.4);
  border-left: 4px solid #ff9800;
  animation: pulse-warning 2s ease-in-out infinite;
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

@keyframes pulse-warning {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

.nav-deviation-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.nav-deviation-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-deviation-title {
  font-size: 1rem;
  font-weight: 700;
  color: #ff6b6b;
  line-height: 1.2;
}

.nav-deviation-distance {
  font-size: 0.85rem;
  color: #ff9800;
  font-weight: 600;
  line-height: 1.2;
  opacity: 0.9;
}

/* Manual Mode Indicator */
.nav-manual-mode-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 193, 7, 0.2);
  padding: 10px 12px;
  border-radius: 8px;
  margin-top: 8px;
  border: 1px solid rgba(255, 193, 7, 0.4);
  border-left: 4px solid #ffc107;
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

.manual-mode-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.manual-mode-text {
  flex: 1;
  font-size: 0.85rem;
  color: #ffc107;
  font-weight: 600;
  line-height: 1.2;
}

.manual-mode-reset-btn {
  background: rgba(255, 193, 7, 0.3);
  border: 1px solid rgba(255, 193, 7, 0.5);
  color: #ffc107;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.manual-mode-reset-btn:hover {
  background: rgba(255, 193, 7, 0.4);
  border-color: rgba(255, 193, 7, 0.7);
  transform: translateY(-1px);
}

.manual-mode-reset-btn:active {
  transform: translateY(0);
}

/* Location Buttons */
.location-buttons {
  position: absolute;
  top: 90px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Adjust location buttons position when nav banner is shown - account for banner height */
.nav-banner ~ .location-buttons {
  top: 160px; /* Increased to ensure buttons are below banner even with deviation warning */
}

.location-btn {
  position: relative;
  background: rgba(15, 22, 32, 0.7);
  color: #eef4ff;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 50%;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  cursor: pointer;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  transition: all 0.2s ease;
}

.location-btn:hover {
  background: rgba(15, 22, 32, 0.85);
  transform: scale(1.05);
}

.location-btn:hover .location-btn-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(-50%) translateX(0);
}

.location-btn:first-child {
  background: linear-gradient(135deg, rgba(0, 198, 255, 0.3) 0%, rgba(0, 114, 255, 0.3) 100%);
  border-color: rgba(0, 198, 255, 0.4);
}

.location-btn:last-child {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.3) 0%, rgba(247, 124, 0, 0.3) 100%);
  border-color: rgba(255, 152, 0, 0.4);
}

.location-btn.loading {
  cursor: wait;
  opacity: 0.7;
}

.location-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.location-btn .spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

.location-btn-tooltip {
  position: absolute;
  right: calc(100% + 12px);
  top: 50%;
  transform: translateY(-50%) translateX(-8px);
  background: rgba(15, 22, 32, 0.95);
  color: #eef4ff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease, transform 0.2s ease;
  pointer-events: none;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.2);
  z-index: 1001;
}

.location-btn-tooltip::after {
  content: '';
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  border: 5px solid transparent;
  border-left-color: rgba(15, 22, 32, 0.95);
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
  border: 1px solid rgba(255,255,255,0.25);
  border-bottom: none;
  border-radius: 14px 14px 0 0;
  box-shadow: 0 -10px 30px rgba(0,0,0,0.35);
  z-index: 1002;
  transition: transform 220ms ease;
  will-change: transform;
  touch-action: none;
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
  touch-action: none;
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
  border: 1px solid rgba(255,255,255,0.25);
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
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 10px;
  padding: 12px;
}

.current-poi-card h4 {
  margin: 0 0 10px 0;
  text-align: center;
}

.cancel-nav-btn {
  width: 100%;
  background: linear-gradient(135deg, #ff3db3 0%, #ff5f5f 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px;
  font-weight: bold;
  font-size: 0.95rem;
  cursor: pointer;
  margin-top: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  transition: transform 0.1s ease, box-shadow 0.2s ease;
}

.cancel-nav-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.3);
}

.cancel-nav-btn:active {
  transform: translateY(0);
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
  border: 1px solid rgba(255,255,255,0.25);
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
  margin-bottom: 8px;
  transition: transform 0.1s ease, box-shadow 0.2s ease;
}

.confirm-route-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 200, 83, 0.3);
}

.confirm-route-btn:active {
  transform: translateY(0);
}

.generate-new-route-btn {
  width: 100%;
  background: linear-gradient(135deg, #6a5cff 0%, #ff3db3 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: transform 0.1s ease, box-shadow 0.2s ease;
}

.generate-new-route-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(106, 92, 255, 0.3);
}

.generate-new-route-btn:active:not(:disabled) {
  transform: translateY(0);
}

.generate-new-route-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  border: 1px solid rgba(255,255,255,0.25);
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


/* Advanced QUITE OK HONSETLY. NOT GOOD LOOKING; BUT OK.*/
.adv-toggle {
  background: linear-gradient(135deg, rgba(106, 92, 255, 0.25), rgba(176, 108, 255, 0.2));
  color: #f8f8ff;
  border: 1px solid rgba(176, 108, 255, 0.45);
  border-radius: 10px;
  padding: 9px 14px;
  font-size: 0.95rem;
  font-weight: 800;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
  box-shadow: 0 3px 10px rgba(106, 92, 255, 0.25);
  transition: all 0.18s ease;
}

.adv-toggle::before {
  content: "⚙️✨";
  font-size: 1.1em;
}

.adv-toggle::after {
  content: "▼";
  font-size: 0.8em;
  opacity: 0.85;
  margin-left: 4px;
  transform: translateY(1px);
}

.adv-toggle:hover {
  background: linear-gradient(135deg, rgba(106, 92, 255, 0.35), rgba(176, 108, 255, 0.28));
  border-color: rgba(176, 108, 255, 0.65);
  box-shadow: 0 4px 14px rgba(106, 92, 255, 0.35);
  transform: translateY(-1px);
}

/* Advanced panel — slightly more defined, harmonious */
.advanced-box {
  margin-top: 10px;
  margin-bottom: 10px;
  padding: 12px;
  border: 1px solid rgba(106, 92, 255, 0.25);
  border-radius: 10px;
  background: rgba(106, 92, 255, 0.08);
}

.advanced-box h4 {
  margin: 0 0 8px 2px;
  font-size: 1.05rem;
  font-weight: 800;
  color: #c6b6ff;
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
  border: 1px solid rgba(255,255,255,0.25);
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
  border: 1px solid rgba(255,255,255,0.25);
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
  border: 1px solid rgba(255,255,255,0.2);
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
  opacity: 0.95;
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
  color: #ffb6f4;
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

/* .poi-details-sheet { display:flex; flex-direction:column; gap:12px; } */


.poi-sheet-header { display:flex; align-items:center; justify-content:center; position:relative; }
.close-sheet-btn {
  position:absolute; right:4px; top:-4px; border:none; background:transparent; color:#fff; font-size:1.1rem; cursor:pointer;
}
.poi-meta { 
  margin-bottom: 0; 
}


.poi-line { font-size:.9rem; margin-bottom:4px; }
.poi-cats { font-size:.8rem; opacity:.8; margin-bottom:6px; }
.poi-extract { font-size:.9rem; line-height:1.35; margin:6px 0; }
.poi-links a, .poi-wiki a { color:#6a5cff; text-decoration:none; }
.poi-actions { display:flex; flex-direction:column; gap:8px; }
.poi-actions .row { display:flex; gap:8px; }
.action { flex:1; padding:10px; border:none; border-radius:8px; cursor:pointer; background:rgba(255,255,255,0.15); color:#eef4ff; }
.action.primary { background: linear-gradient(135deg,#6a5cff 0%, #3db3ff 100%); }
.action.danger  { background: linear-gradient(135deg,#ff3db3 0%, #ff5f5f 100%); }


.poi-details-sheet {
  /* already present… we’ll extend it */
  display: grid;                         /* NEW: 3-row grid */
  grid-template-rows: auto 1fr auto;     /* header / scroll / footer */
  height: 58vh;
  min-height: 280px;
  overflow: hidden;
  /* keep your existing props here (background, etc.) */
}


.poi-sheet-header {
  position: sticky;
  top: 0;
  background: rgba(15, 22, 32, 0.65);
  backdrop-filter: blur(6px);
  z-index: 2;
  text-align: center;
  padding: 6px 32px;
  border-bottom: 1px solid rgba(106, 92, 255, 0.4);
}



:root{
  /* Height of your bottom tab bar/home indicator clearance */
  --footer-offset: calc(72px + env(safe-area-inset-bottom));
}

.poi-scroll{
  overflow-y: auto;
  padding: 8px 6px;
  /* leave room for sticky footer + a little breathing space */
  padding-bottom: calc(12px + var(--footer-offset));
}

.poi-actions.sticky{
  position: sticky;
  bottom: var(--footer-offset);   /* <- sits above your tab bar */
  z-index: 2;
  padding: 12px 8px 14px;
  background: linear-gradient(180deg, rgba(15,22,32,0.04), rgba(15,22,32,0.7));
  border-top: 1px solid rgba(255,255,255,0.12);
  backdrop-filter: blur(4px);
}


/* Small comfort tweaks for buttons */
.poi-actions .row {
  display: flex;
  gap: 10px;                             /* slightly bigger gap */
}

.action {
  flex: 1;
  padding: 11px;                         /* just a touch more height */
  border: none;
  border-radius: 8px;
  cursor: pointer;
  background: rgba(255,255,255,0.15);
  color: #eef4ff;
}



.poi-extract.clamped {
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.readmore-btn {
  background: none;
  border: none;
  color: #1805f1;
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0;
}

.leaflet-marker-icon.pulse {
  animation: pulse-marker 1.4s infinite;
}

@keyframes pulse-marker {
  0% { transform: scale(1); filter: drop-shadow(0 0 0 rgba(106, 92, 255, 0.6)); }
  70% { transform: scale(1.1); filter: drop-shadow(0 0 12px rgba(106, 92, 255, 0.9)); }
  100% { transform: scale(1); filter: drop-shadow(0 0 0 rgba(106, 92, 255, 0.6)); }
}
.poi-sheet-header {
  border-bottom: 1px solid rgba(106, 92, 255, 0.4);
}

.read-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
  flex-wrap: wrap;
}

/* .link-pill {
  appearance: none;
  border: 1px solid rgba(106, 92, 255, 0.65);
  background: rgba(106, 92, 255, 0.18);
  color: #e9e6ff;            
  font-weight: 800;           
  font-size: 0.9rem;
  padding: 6px 10px;
  border-radius: 10px;
  cursor: pointer;
  text-decoration: none;
  transition: transform .07s ease, border-color .15s ease, background .15s ease;
}

.link-pill:hover {
  transform: translateY(-1px);
  border-color: rgba(106, 92, 255, 0.9);
  background: rgba(106, 92, 255, 0.28);
}  */

/* new */
.read-actions { display:flex; align-items:center; gap:10px; margin-top:6px; flex-wrap:wrap; }
.text-link {
  background:none; border:none; padding:0;
  color:#e9e6ff; opacity:.95;
  text-decoration:underline; font-weight:600; font-size:.95rem;
  cursor:pointer;
}
.text-link:hover { opacity:1; }
.sep { opacity:.7; }
/* new ends */

.views {
  font-size: 0.9rem;
  font-weight: 700;
  color: #e9e6ff;
  opacity: 0.95;
  margin-bottom: 0px;
  padding-bottom: 0;
}

/* the old readmore button can be removed or kept unused */
.readmore-btn { display: none; }

.inline-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 6px;
}

/* The link-style buttons (matches old "Read more" feel) */
.read-inline {
  appearance: none;
  background: none;
  border: none;
  color: #e9e6ff;
  opacity: 0.95;
  font-size: 0.9rem;
  text-decoration: underline;
  padding: 0;
  cursor: pointer;
}

.read-inline:hover {
  opacity: 1;
}

/* separator dot between the two links when both exist */
.dot-sep {
  margin: 0 6px;
  opacity: 0.7;
}

/* views moved to own row for cleaner layout (no overlap with links) */
.views-row {
  font-size: 0.9rem;
  font-weight: 700;
  color: #e9e6ff;
  opacity: 0.95;
}

/* .categories-line { margin-top: 2px; } */

.categories-line {
  margin-top: 0px;
  opacity: .95;
}

/* .categories-line.compact .cats-text {
  display: -webkit-box;
  -webkit-line-clamp: 1;        
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: .95;
}
 */
.categories-line.clamped {
  display: -webkit-box;
  -webkit-line-clamp: 1;        /* keep to 1 line; change to 2 if you prefer */
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* optional: hint it’s truncating when compact */
.categories-line.compact { opacity: .95; }


/* keep horizontal spacing, kill the vertical gap between rows */
/* .read-actions{ gap: 0 10px; }     
.categories-line{ margin-top: 0; } 
 */
.read-actions { gap: 3px 10px; }   /* row-gap 2px, column-gap 10px */
.categories-line { margin-top: 1px; line-height: 1.18; }
.views { line-height: 1.18; }

/* Compact card spacing */
.time-card.time-compact { padding: 8px 10px; gap: 6px; }

/* Title + input on one row */
.time-header {
  display: grid;
  grid-template-columns: auto 1fr auto; /* title | flex | input */
  align-items: center;
  gap: 8px;
}

/* Keep sizes; just tighter line height */
.time-title-compact { font-size: .95rem; font-weight: 800; line-height: 1.1; }

/* Keep input size, but no extra margins */
.time-time.large {
  font-size: 1.05rem;
  font-weight: 800;
  padding: 6px 8px;
  border-radius: 8px;
  border: none;
  margin: 0;
}

/* Tight summary line */
.time-subline {
  display: flex;
  gap: 6px;
  justify-content: center;
  font-size: .85rem;
  opacity: .9;
  margin-top: 2px;
}





.route-summary {
  position: relative;
}

.poi-browse-controls {
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  gap: 6px;
}

.browse-btn {
  background: #f2f3f5;
  border: 0;
  border-radius: 8px;
  padding: 4px 8px;
  font-size: .9rem;
  cursor: pointer;
}
.browse-btn:disabled { opacity: .4; cursor: default; }

.next-peek {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f7f8ff;
}
.peek-label {
  font-size: .75rem;
  opacity: .7;
  margin-bottom: 2px;
}
.peek-title {
  font-weight: 600;
  line-height: 1.2;
}

.poi-quick-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}
.nav-mode.arrived .poi-navigation-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.nav-btn.next {
  background: #6a5cff;
  color: #fff;
  border: 0;
  border-radius: 8px;
  padding: 8px 12px;
}

.peek-title { color: #0b1220; }

.peek-label{ color: #0b1220; }



.poi-quick-actions.tight {
  margin-top: 8px;
  display: grid;
  grid-template-columns: 1fr 1fr; /* equal width buttons */
  gap: 8px;
}

/* a bit smaller than big destructive footer button */
.poi-quick-actions.tight .action {
  padding: 10px;
  border-radius: 10px;
  font-weight: 800;
}

/* optional: lighter cancel look if you prefer */
.action.danger.ghost {
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 99, 132, 0.5);
  color: #ffd7e0;
}
</style>
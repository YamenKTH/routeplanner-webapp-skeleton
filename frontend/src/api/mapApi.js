import { api } from "./apiClient.js";

/**
 * Load POIs around a given location
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @param {number} radius_m - Radius in meters
 * @param {Object} catWeights - Category weights for scoring
 * @returns {Promise<Object>} Response data with features array
 */
export async function loadPois(lat, lon, radius_m, catWeights) {
  const payload = {
    lat,
    lon,
    radius_m,
    cat_weights: { ...catWeights },
  };

  const { data } = await api.post("/api/pois", payload);
  return data;
}

/**
 * Build a tour/route with given parameters
 * @param {Object} params - Tour parameters
 * @param {number} params.lat - Start latitude
 * @param {number} params.lon - Start longitude
 * @param {number} params.time_min - Time in minutes
 * @param {number} params.radius_m - Radius in meters
 * @param {boolean} params.roundtrip - Whether it's a round trip
 * @param {number|null} params.end_lat - End latitude (null for round trip)
 * @param {number|null} params.end_lon - End longitude (null for round trip)
 * @param {string} params.router - Router type (e.g., "osrm")
 * @param {string} params.router_url - Router URL
 * @param {boolean} params.snap_path - Whether to snap path
 * @param {Object} params.cat_weights - Category weights
 * @returns {Promise<Object>} Response data with route information
 */
export async function buildTour({
  lat,
  lon,
  time_min,
  radius_m,
  roundtrip,
  end_lat,
  end_lon,
  router = "osrm",
  router_url = "http://osrm:5000",
  snap_path = true,
  cat_weights,
}) {
  const payload = {
    lat: Number(lat),
    lon: Number(lon),
    time_min: Number(time_min),
    radius_m: Number(radius_m),
    roundtrip,
    end_lat: roundtrip ? null : (end_lat ? Number(end_lat) : null),
    end_lon: roundtrip ? null : (end_lon ? Number(end_lon) : null),
    router,
    router_url,
    snap_path,
    cat_weights: { ...cat_weights },
  };

  const { data } = await api.post("/api/tour", payload);
  return data;
}


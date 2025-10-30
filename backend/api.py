# backend/api.py
import os
import sys
import importlib
import requests
from typing import Optional, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Scorer import Scorer
from app_explore import load_cached_area, haversine_m
from app_tour import (
    HaversineRouter,
    OSRMRouter,
    simple_greedy_solver,
    build_sites,
    feasible_sites_mask,
    osrm_route_leg,
    osrm_route_leg_detailed,
)

# Ensure the folder containing api.py is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

def _import_or_none(name: str):
    try:
        return importlib.import_module(name)
    except Exception as e:
        print(f"[IMPORT FAIL] {name}: {e}")
        return None

Scorer_mod      = _import_or_none("Scorer")
app_explore_mod = _import_or_none("app_explore")
app_tour_mod    = _import_or_none("app_tour")
clean_db_mod    = _import_or_none("cleanDatabase")

HAS_REAL_STACK = all([Scorer_mod, app_explore_mod, app_tour_mod, clean_db_mod])

# ---------- Pydantic DTOs ----------
class PoisRequest(BaseModel):
    lat: float
    lon: float
    radius_m: int = 700
    cat_weights: Optional[Dict[str, float]] = None

class TourRequest(BaseModel):
    lat: float
    lon: float
    time_min: int
    radius_m: int = 700
    roundtrip: bool = True
    end_lat: Optional[float] = None
    end_lon: Optional[float] = None
    router: str = "haversine"  # "haversine" | "osrm"
    router_url: Optional[str] = None
    dwell_sec: int = 180
    cat_weights: Optional[Dict[str, float]] = None
    snap_path: bool = False
    walk_speed_mps: float = 1.35

app = FastAPI(title="RoutePlanner Web API", version="0.2.0")

# CORS for Vite dev server
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8080", 
    "http://127.0.0.1:8080"    
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- OSRM snapped path helper ----------
def _osrm_leg_geojson_coords(base_url: str, a_lat: float, a_lon: float,
                             b_lat: float, b_lon: float, profile: str = "foot"):
    """
    Fetch a snapped route leg (as GeoJSON coordinates) between two points using OSRM.
    """
    url = f"{base_url.rstrip('/')}/route/v1/{profile}/{a_lon},{a_lat};{b_lon},{b_lat}?overview=full&geometries=geojson"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        js = r.json()
        routes = js.get("routes", [])
        if not routes:
            return []
        return routes[0]["geometry"]["coordinates"]  # [[lon,lat], ...]
    except Exception as e:
        print(f"[OSRM] route leg failed: {e} -> {url}")
        return []

# ---------- Helpers for real stack ----------
def _real_load_pois(lat: float, lon: float, radius_m: int, cat_weights: Dict[str, float]):
    Scorer = getattr(Scorer_mod, "Scorer")
    load_cached_area = getattr(app_explore_mod, "load_cached_area")
    scorer = Scorer(cat_weights=cat_weights or {})
    db_path = os.getenv("CACHE_DB") or getattr(app_explore_mod, "DEFAULT_DB", "out/stockholm_wiki.db")
    pois, wiki_views, details_map = load_cached_area(db_path, lat, lon, radius_m, scorer)

    features = []
    for p in pois:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]},
            "properties": {
                "xid": getattr(p, "xid", None),
                "name": getattr(p, "name", ""),
                "kinds": getattr(p, "kinds", ""),
                "raw_rate": getattr(p, "raw_rate", None),
                "score": getattr(p, "score", None),
                "wiki": wiki_views.get(getattr(p, "xid", ""), {}),
                "details": details_map.get(getattr(p, "xid", ""), {})
            }
        })
    return {"type": "FeatureCollection", "features": features}

""" def _real_build_tour(req: TourRequest):


    Scorer = getattr(Scorer_mod, "Scorer")
    scorer = Scorer(cat_weights=req.cat_weights or {})
    load_cached_area = getattr(app_explore_mod, "load_cached_area")
    db_path = os.getenv("CACHE_DB") or getattr(app_explore_mod, "DEFAULT_DB", "out/stockholm_wiki.db")
    pois, wiki_views, details_map = load_cached_area(db_path, req.lat, req.lon, req.radius_m, scorer)

    # app_tour3 helpers
    HaversineRouter = getattr(app_tour_mod, "HaversineRouter")
    OSRMRouter = getattr(app_tour_mod, "OSRMRouter")
    simple_greedy_solver = getattr(app_tour_mod, "simple_greedy_solver")
    build_sites = getattr(app_tour_mod, "build_sites")
    feasible_sites_mask = getattr(app_tour_mod, "feasible_sites_mask")

    start = (req.lat, req.lon)
    end = None if req.roundtrip else ((req.end_lat, req.end_lon) if req.end_lat and req.end_lon else None)

    router = HaversineRouter(walk_speed_mps=req.walk_speed_mps) if req.router != "osrm" \
        else OSRMRouter(req.router_url or os.getenv("OSRM_URL") or "http://localhost:5000")

    sites = build_sites(pois)
    coords = [start] + [(s.lat, s.lon) for s in sites]
    site_idx_offset = 1
    end_index = None
    if end is not None:
        coords.append(end)
        end_index = len(coords) - 1

    # Compute OSRM matrix or Haversine matrix
    M = router.time_matrix_seconds(coords)
    print(f"Calculated time matrix with {len(coords)} points using {req.router}")

    mask = feasible_sites_mask(
        start_idx=0, end_idx=end_index, site_idx_offset=site_idx_offset,
        M=M, budget_s=int(req.time_min * 60),
        open_end=(not req.roundtrip) and (end is None),
        n_sites=len(sites)
    )

    tour = simple_greedy_solver(
        start, end, int(req.time_min * 60), sites,
        M=M, site_idx_offset=site_idx_offset, end_index=end_index,
        roundtrip=req.roundtrip, candidate_mask=mask,
        dwell_time_s=req.dwell_sec, coords=coords, walk_speed_mps=req.walk_speed_mps
    )

    # Collect stop coordinates
    id_to_site = {s.id: s for s in sites}
    stops = [(req.lat, req.lon)]
    for sid in tour.site_ids:
        s = id_to_site[sid]
        stops.append((s.lat, s.lon))
    if end is not None:
        stops.append(end)

    # ----- snapped geometry if requested -----
    if req.router == "osrm" and req.snap_path:
        base = req.router_url or os.getenv("OSRM_URL") or "http://localhost:5000"
        snapped = []
        for i in range(len(stops) - 1):
            a_lat, a_lon = stops[i]
            b_lat, b_lon = stops[i + 1]
            leg = _osrm_leg_geojson_coords(base, a_lat, a_lon, b_lat, b_lon, profile="foot")
            if not leg:
                continue
            if snapped:
                snapped.extend(leg[1:])  # avoid duplicate points
            else:
                snapped.extend(leg)
        path_geo = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": snapped},
            "properties": {"snapped": True, "router": "osrm"}
        }
    else:
        # Straight-line fallback
        line = [[lon, lat] for (lat, lon) in stops]
        path_geo = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": line},
            "properties": {"snapped": False, "router": req.router}
        }

    return {
        "tour": {
            "site_ids": tour.site_ids,
            "leg_times_s": getattr(tour, "leg_times_s", []),
            "total_time_s": getattr(tour, "total_time_s", None),
        },
        "stops": [{"lat": lat, "lon": lon} for (lat, lon) in stops],
        "path": path_geo
    } """

def _real_build_tour(req: TourRequest):
    start = (float(req.lat), float(req.lon))
    roundtrip = bool(req.roundtrip)

    end = None
    if not roundtrip and (req.end_lat is not None) and (req.end_lon is not None):
        end = (float(req.end_lat), float(req.end_lon))

    # Per-request scorer (stateless)
    #scorer = Scorer(cat_weights=req.cat_weights or {})  #BUT LETS OVERWRITE IT FOR NOW!!!!
    #
    scorer = Scorer()

    db_path = (getattr(req, "cache_db", None)
               or os.getenv("CACHE_DB")
               or "out/stockholm_wiki.db")

    pois, wiki_views, details_map = load_cached_area(
        db_path, start[0], start[1], int(req.radius_m), scorer
    )

    sites = build_sites(pois)
    site_lookup = {s.id: s for s in sites}

    if req.router == "osrm":
        base_url = req.router_url or os.getenv("OSRM_URL")
        if not base_url:
            raise SystemExit("Please provide --router-url for OSRM, e.g. http://localhost:5000")
        router = OSRMRouter(base_url)
    else:
        router = HaversineRouter(walk_speed_mps=float(req.walk_speed_mps))

    budget_s = int(req.time_min) * 60

    coords = [start] + [(s.lat, s.lon) for s in sites]
    site_idx_offset = 1
    end_coord = start if (roundtrip and end is None) else end
    end_index = None
    if end_coord is not None:
        coords.append(end_coord)
        end_index = len(coords) - 1

    print("BEGINNING TO CALCULATE M")
    M = router.time_matrix_seconds(coords)

    open_end = (not roundtrip) and (end is None)
    mask = feasible_sites_mask(
        start_idx=0,
        end_idx=end_index,
        site_idx_offset=site_idx_offset,
        M=M,
        budget_s=budget_s,
        open_end=open_end,
        n_sites=len(sites),
    )

    tour = simple_greedy_solver(
        start=start,
        end=end,
        budget_s=budget_s,
        sites=sites,
        M=M,
        site_idx_offset=site_idx_offset,
        end_index=end_index,
        roundtrip=roundtrip,
        candidate_mask=mask,
        dwell_time_s=int(req.dwell_sec),
        coords=coords,
        walk_speed_mps=float(req.walk_speed_mps),
        backtrack_angle_deg=150.0,
        backtrack_penalty_per_m=0.15,
        edge_reuse_penalty_s=20.0,
    )

    # stops: start -> sites -> [end_coord?]
    id_to_site = {s.id: s for s in sites}
    stops_latlon = [start] + [(id_to_site[sid].lat, id_to_site[sid].lon) for sid in tour.site_ids]
    if end_coord is not None:
        stops_latlon.append(end_coord)

    # 2) Build snapped or straight path (GeoJSON lon/lat order) + navigation info
    navigation_legs = []  # Detailed info for each leg
    if req.router == "osrm" and getattr(req, "snap_path", False):
        base = req.router_url or os.getenv("OSRM_URL")
        coords_lonlat = []
        for i in range(len(stops_latlon) - 1):
            # Get detailed route info with street names
            detailed = osrm_route_leg_detailed(base, stops_latlon[i], stops_latlon[i + 1])
            seg_latlon = detailed["coords_latlon"]
            seg_lonlat = [[lon, lat] for (lat, lon) in seg_latlon]
            coords_lonlat.extend(seg_lonlat if not coords_lonlat else seg_lonlat[1:])
            
            # Store navigation info for this leg
            navigation_legs.append({
                "from_stop_index": i,
                "to_stop_index": i + 1,
                "distance_m": detailed["distance_m"],
                "duration_s": detailed["duration_s"],
                "next_street_name": None,  # OSRM doesn't reliably provide street names
                "steps": detailed["steps"],
                "coords_latlon": detailed["coords_latlon"],  # Add coordinates for highlighting
            })
        path_geo = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords_lonlat},
            "properties": {"snapped": True, "router": "osrm"},
        }
    else:
        line_lonlat = [[lon, lat] for (lat, lon) in stops_latlon]
        path_geo = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": line_lonlat},
            "properties": {"snapped": False, "router": req.router},
        }

    # 3) Send structured POIs so Vue can build popups with buildPoiPopup(props)
    pois_data = []
    for p in pois:
        pois_data.append({
            "xid": p.xid,
            "name": p.name,
            "lat": p.lat,
            "lon": p.lon,
            "kinds": getattr(p, "kinds", []),
            "raw_rate": getattr(p, "raw_rate", None),
            "score": getattr(p, "score", None),
            "det": details_map.get(p.xid),   # OTM details (addr, extracts, urls)
            "wv": wiki_views.get(p.xid),     # Wikipedia info (title, project, views_365)
            "distance_m": int(haversine_m(start[0], start[1], p.lat, p.lon)),
        })

    # Build ordered POIs used by the route (aligned with tour.site_ids; excludes start/end)
    coord_to_poi = {(round(p.lat, 6), round(p.lon, 6)): p for p in pois}
    route_pois = []
    for sid in tour.site_ids:
        s = id_to_site.get(sid)
        if not s:
            continue
        key = (round(s.lat, 6), round(s.lon, 6))
        p = coord_to_poi.get(key)
        if not p:
            continue
        route_pois.append({
            "xid": p.xid,
            "name": p.name,
            "lat": p.lat,
            "lon": p.lon,
            "kinds": getattr(p, "kinds", []),
            "raw_rate": getattr(p, "raw_rate", None),
            "score": getattr(p, "score", None),
            "det": details_map.get(p.xid),
            "wv": wiki_views.get(p.xid),
            "distance_m": int(haversine_m(start[0], start[1], p.lat, p.lon)),
        })

    # Enrich stops with names and ids (start, poi..., [end])
    enriched_stops = []
    def _shorten(text: Optional[str], limit: int = 220) -> Optional[str]:
        if not text:
            return None
        text = text.strip()
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + "…"

    if stops_latlon:
        enriched_stops.append({
            "lat": stops_latlon[0][0],
            "lon": stops_latlon[0][1],
            "name": "Start",
            "description": "Route start",
            "xid": None,
            "categories": [],
        })
    for i, rp in enumerate(route_pois):
        slat, slon = stops_latlon[i + 1]
        xid = rp.get("xid")
        det = details_map.get(xid) if xid else None
        wv = wiki_views.get(xid) if xid else None
        extract = (det or {}).get("wikipedia_extracts", {}).get("text", None)
        wiki_url = None
        if wv and wv.get("project") and wv.get("title"):
            wiki_url = f"https://{wv['project']}/wiki/{wv['title']}"
        enriched_stops.append({
            "lat": slat,
            "lon": slon,
            "name": rp.get("name") or f"POI {i+1}",
            "xid": xid,
            "description": _shorten(extract, 220),
            "wiki_url": wiki_url,
            "views_365": (wv or {}).get("views_365"),
            "categories": (getattr(coord_to_poi.get((round(slat,6), round(slon,6)), None), "kinds", []) if True else []),
        })
    if len(stops_latlon) > (1 + len(route_pois)):
        slat, slon = stops_latlon[-1]
        enriched_stops.append({
            "lat": slat,
            "lon": slon,
            "name": "End",
            "description": "Route end",
            "xid": None,
            "categories": [],
        })

    # Return
    return {
        "tour": {
            "site_ids": tour.site_ids,
            "leg_times_s": getattr(tour, "leg_times_s", []),
            "total_time_s": getattr(tour, "total_time_s", 0),
            "stop_score": getattr(tour, "stop_score", 0),
            "passby_score": getattr(tour, "passby_score", 0.0),
        },
        "stops": enriched_stops,
        "path": path_geo,
        "navigation_legs": navigation_legs,  # Street names and distances for each leg
        "pois": pois_data,
        "route_pois": route_pois,
        "roundtrip": roundtrip,
        "time_budget_s": budget_s,
    }


# ---------- Mock helpers ----------
def _mock_pois(lat: float, lon: float, radius_m: int, cat_weights: Dict[str, float]):
    import math
    features = []
    for i in range(8):
        angle = i * (2 * math.pi / 8)
        dlat = (radius_m / 111111.0) * math.cos(angle)
        dlon = (radius_m / 111111.0) * math.sin(angle) / max(0.1, abs(math.cos(math.radians(lat))))
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon + dlon, lat + dlat]},
            "properties": {"name": f"Mock POI {i + 1}", "score": 100 - i * 5, "kinds": "poi", "raw_rate": 3}
        })
    return {"type": "FeatureCollection", "features": features}

def _mock_tour(req: TourRequest):
    stops = [(req.lat, req.lon),
             (req.lat + 0.002, req.lon + 0.002),
             (req.lat + 0.004, req.lon - 0.001),
             (req.lat + 0.001, req.lon - 0.003)]
    if req.roundtrip:
        stops.append((req.lat, req.lon))
    line = [[lon, lat] for (lat, lon) in stops]
    return {
        "tour": {"site_ids": [1, 2, 3], "leg_times_s": [300, 420, 390], "total_time_s": 1200},
        "stops": [{"lat": lat, "lon": lon} for (lat, lon) in stops],
        "path": {"type": "Feature", "geometry": {"type": "LineString", "coordinates": line}, "properties": {"snapped": False}}
    }

# ---------- Endpoints ----------
@app.get("/api/health")
def health():
    return {"ok": True, "uses_real_stack": bool(HAS_REAL_STACK)}

@app.post("/api/pois")
def api_pois(req: PoisRequest):
    if HAS_REAL_STACK:
        return _real_load_pois(req.lat, req.lon, req.radius_m, req.cat_weights or {})
    return _mock_pois(req.lat, req.lon, req.radius_m, req.cat_weights or {})

@app.post("/api/tour")
def api_tour(req: TourRequest):
    if HAS_REAL_STACK:
        return _real_build_tour(req)
    return _mock_tour(req)
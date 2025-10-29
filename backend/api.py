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

    # Generate 2-3 routes with different parameter strategies
    route_strategies = [
        {
            "name": "balanced",
            "description": "Balanced route",
            "backtrack_angle_deg": 150.0,
            "backtrack_penalty_per_m": 0.15,
            "edge_reuse_penalty_s": 20.0,
            "dwell_time_s": int(req.dwell_sec),
            "budget_multiplier": 1.0,  # 100% of budget
            "score_multiplier": 1.0,  # Normal scoring
        },
        {
            "name": "score-first",
            "description": "Prioritize high-scoring POIs",
            "backtrack_angle_deg": 150.0,
            "backtrack_penalty_per_m": 0.08,  # Lower penalty allows longer detours for high scores
            "edge_reuse_penalty_s": 15.0,
            "dwell_time_s": int(req.dwell_sec * 0.8),  # Shorter dwell = more stops possible
            "budget_multiplier": 1.0,
            "score_multiplier": 1.5,  # Boost scores to favor high-scoring POIs
        },
        {
            "name": "compact",
            "description": "Compact route with fewer stops",
            "backtrack_angle_deg": 145.0,
            "backtrack_penalty_per_m": 0.20,
            "edge_reuse_penalty_s": 25.0,
            "dwell_time_s": int(req.dwell_sec * 1.5),  # Longer dwell = fewer stops
            "budget_multiplier": 0.9,  # 90% of budget = shorter route
            "score_multiplier": 1.0,
        },
    ]

    # Generate routes with different strategies
    tours = []
    for strategy in route_strategies:
        # Apply score multiplier to sites for this strategy (create modified copies)
        if strategy["score_multiplier"] != 1.0:
            from app_tour import Site
            modified_sites = [
                Site(
                    id=site.id,
                    name=site.name,
                    lat=site.lat,
                    lon=site.lon,
                    base_score=site.base_score * strategy["score_multiplier"],
                    members=site.members,
                    kinds=getattr(site, "kinds", []),
                    raw_rate=getattr(site, "raw_rate", None),
                )
                for site in sites
            ]
        else:
            modified_sites = sites
        
        # Use modified budget for this strategy
        strategy_budget = int(budget_s * strategy["budget_multiplier"])
        
        tour = simple_greedy_solver(
            start=start,
            end=end,
            budget_s=strategy_budget,
            sites=modified_sites,
            M=M,
            site_idx_offset=site_idx_offset,
            end_index=end_index,
            roundtrip=roundtrip,
            candidate_mask=mask,
            dwell_time_s=strategy["dwell_time_s"],
            coords=coords,
            walk_speed_mps=float(req.walk_speed_mps),
            backtrack_angle_deg=strategy["backtrack_angle_deg"],
            backtrack_penalty_per_m=strategy["backtrack_penalty_per_m"],
            edge_reuse_penalty_s=strategy["edge_reuse_penalty_s"],
        )
        tours.append((tour, strategy))

    # stops: start -> sites -> [end_coord?]
    id_to_site = {s.id: s for s in sites}
    
    # Create a lookup map from xid to POI data for easy matching
    xid_to_poi_data = {p.xid: {
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
    } for p in pois}

    # Helper function to build a route response from a tour
    def build_route_response(tour, strategy_info):
        # Build stops with full information
        stops = []
        
        # 1. Start position (no POI data, just coordinates)
        stops.append({
            "lat": start[0],
            "lon": start[1],
            "is_start": True,
            "is_end": False
        })
        
        # 2. POI stops (merge with POI data)
        for sid in tour.site_ids:
            site = id_to_site[sid]
            poi_data = xid_to_poi_data.get(sid, {})
            # Merge site info with POI data
            stop_info = {
                "lat": site.lat,
                "lon": site.lon,
                "xid": sid,
                "name": site.name or poi_data.get("name", "Unnamed"),
                "kinds": site.kinds or poi_data.get("kinds", []),
                "raw_rate": site.raw_rate or poi_data.get("raw_rate"),
                "score": site.base_score or poi_data.get("score"),
                "det": poi_data.get("det"),
                "wv": poi_data.get("wv"),
                "distance_m": poi_data.get("distance_m"),
                "is_start": False,
                "is_end": False
            }
            stops.append(stop_info)
        
        # 3. End position (if exists and different from start)
        if end_coord is not None and end_coord != start:
            stops.append({
                "lat": end_coord[0],
                "lon": end_coord[1],
                "is_start": False,
                "is_end": True
            })

        # Build snapped or straight path (GeoJSON lon/lat order)
        stops_latlon = [(s["lat"], s["lon"]) for s in stops]
        
        if req.router == "osrm" and getattr(req, "snap_path", False):
            base = req.router_url or os.getenv("OSRM_URL")
            coords_lonlat = []
            for i in range(len(stops_latlon) - 1):
                seg_latlon, _, _ = osrm_route_leg(base, stops_latlon[i], stops_latlon[i + 1])  # [[lat,lon],...]
                seg_lonlat = [[lon, lat] for (lat, lon) in seg_latlon]
                coords_lonlat.extend(seg_lonlat if not coords_lonlat else seg_lonlat[1:])
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

        # Calculate total distance and time
        total_time_s = getattr(tour, "total_time_s", 0)
        leg_times_s = getattr(tour, "leg_times_s", [])
        
        # Approximate distance from leg times (assuming walk_speed_mps)
        total_distance_m = sum(leg_times_s) * float(req.walk_speed_mps) if leg_times_s else 0
        total_distance_km = round(total_distance_m / 1000.0, 1) if total_distance_m > 0 else 0
        time_min = round(total_time_s / 60.0) if total_time_s > 0 else 0

        return {
            "id": strategy_info["name"],
            "name": strategy_info["name"],
            "description": strategy_info["description"],
            "tour": {
                "site_ids": tour.site_ids,
                "leg_times_s": leg_times_s,
                "total_time_s": total_time_s,
                "stop_score": getattr(tour, "stop_score", 0),
                "passby_score": getattr(tour, "passby_score", 0.0),
            },
            "stops": stops,
            "path": path_geo,
            "distance": f"{total_distance_km}",
            "time": f"{time_min} min",
            "stops_count": len([s for s in stops if not s.get("is_start") and not s.get("is_end")]),
        }

    # Build route responses for all tours
    routes = [build_route_response(tour, strategy) for tour, strategy in tours]

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

    # Return routes as a list
    return {
        "routes": routes,
        "pois": pois_data,  # Shared POI data for all routes
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
    # Mock 3 routes with slight variations
    base_stops = [(req.lat, req.lon),
                  (req.lat + 0.002, req.lon + 0.002),
                  (req.lat + 0.004, req.lon - 0.001),
                  (req.lat + 0.001, req.lon - 0.003)]
    if req.roundtrip:
        base_stops.append((req.lat, req.lon))
    
    routes = []
    for i in range(3):
        # Slight variations for each route
        offset = i * 0.0005
        stops = [(req.lat + offset, req.lon + offset),
                 (req.lat + 0.002 + offset, req.lon + 0.002),
                 (req.lat + 0.004 + offset, req.lon - 0.001),
                 (req.lat + 0.001, req.lon - 0.003 + offset)]
        if req.roundtrip:
            stops.append((req.lat + offset, req.lon + offset))
        line = [[lon, lat] for (lat, lon) in stops]
        
        routes.append({
            "id": f"mock_{i}",
            "name": ["balanced", "explore", "efficient"][i],
            "description": f"Mock route {i + 1}",
            "tour": {"site_ids": [1, 2, 3], "leg_times_s": [300 + i*10, 420 + i*10, 390 + i*10], "total_time_s": 1200 + i*30, "stop_score": 100 + i*10},
            "stops": [{"lat": lat, "lon": lon, "is_start": idx == 0, "is_end": idx == len(stops) - 1} for idx, (lat, lon) in enumerate(stops)],
            "path": {"type": "Feature", "geometry": {"type": "LineString", "coordinates": line}, "properties": {"snapped": False}},
            "distance": f"{2.5 + i*0.5}",
            "time": f"{20 + i*2} min",
            "stops_count": len([s for s in stops if len(stops) > 2])
        })
    
    return {
        "routes": routes,
        "pois": [],
        "roundtrip": req.roundtrip,
        "time_budget_s": 1200,
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
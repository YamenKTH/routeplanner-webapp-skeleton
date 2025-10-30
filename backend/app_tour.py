from __future__ import annotations
import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import folium
import hashlib
import json
import concurrent.futures
import requests
from threading import Lock
from typing import Iterable
import html
from dataclasses import dataclass, field


# Reuse your existing pieces
#from app_explore import OpenTripMapClient, Place, haversine_m  # keep files in same folder
from app_explore import Place, haversine_m, load_cached_area
from Scorer import Scorer


#------------------------------------------------------------------------------
# Config / defaults
DEFAULT_WALK_SPEED_MPS = 1.35  # ~4.86 km/h; used only by fallback router
OUTDIR_DEFAULT = "out"

#------------------------------------------------------------------------------
# Data models for tour 
@dataclass
class Site:
    #Routing node (currently 1:1 with a Place. we may add micro-clusters later)

    id: str 
    name: str
    lat: float
    lon: float
    base_score: float           
    members: List[Tuple[str, float]]  # (xid, weight) for attribution; 1 item for now

    kinds: List[str] = field(default_factory=list)
    raw_rate: Optional[float] = None                #OTM Rating

@dataclass
class Tour:
    site_ids: List[str]              # ordered (start .. end) inc. start/end ids
    leg_times_s: List[int]           # len = len(site_ids)-1
    stop_score: float
    passby_score: float              # 0.0 for now; may add this later!
    contributions: Dict[str, float]  # xid -> contributed score (for now, visited sites only)  (if micro clustering!)
    total_time_s: int 

#------------------------------------------------------------------------------
# DISPLAY HELPERS:
def _popup_html_for_place(
    name: str,
    xid: Optional[str],
    lat: float,
    lon: float,
    origin_lat: float,
    origin_lon: float,
    kinds: Optional[List[str]],
    raw_rate: Optional[float],
    det: Optional[dict],
    wv: Optional[dict],
    score: Optional[float] = None,  #The actual score we want to display
) -> str:
    """Faithful copy of explorer popup composition."""
    d = int(haversine_m(origin_lat, origin_lon, lat, lon))
    kinds_str = ", ".join([k for k in (kinds or [])[:6]])

    det = det or {}
    addr = det.get("address", {}) if isinstance(det, dict) else {}
    addr_line = ", ".join(filter(None, [
        addr.get("house_number"), addr.get("road"), addr.get("city")
    ]))

    wiki_extract = det.get("wikipedia_extracts", {}).get("text") if isinstance(det, dict) else None
    if wiki_extract and len(wiki_extract) > 280:
        wiki_extract = wiki_extract[:280] + "…"

    otm_url = det.get("otm") or det.get("url") or (f"https://opentripmap.com/en/card?xid={xid}" if xid else "#")

    if score is None:
        score = 0
    wiki_line = ""
    if wv and wv.get("project") and wv.get("title"):
        wp_url = f"https://{wv['project']}/wiki/{wv['title']}"
        wiki_line = (
            f"📖 Wikipedia views (365d): <b>{int(wv.get('views_365',0)):,}</b> "
            f"&nbsp;|&nbsp; Score: <b>{int(score)}</b> "
            f"&nbsp;•&nbsp; <a target='_blank' href='{html.escape(wp_url)}'>Open article</a>"
        )

    html_popup = f"""
        <b>{html.escape(name or 'Unnamed')}</b><br/>
        OTM rate: {raw_rate if raw_rate is not None else ''} &nbsp;•&nbsp; Distance: {d} m<br/>
        <small>{html.escape(kinds_str)}</small><br/>
        {html.escape(addr_line) if addr_line else ''}
        <div style='margin-top:6px'>{html.escape(wiki_extract) if wiki_extract else ''}</div>
        <div style='margin-top:6px'>{wiki_line}</div>
        <div style='margin-top:6px'><a target='_blank' href='{html.escape(otm_url)}'>Open in OpenTripMap</a></div>
    """
    return html_popup

#------------------------------------------------------------------------------
#RANDOM HELPERS:

import math
def _bearing_rad(a, b):
    lat1 = math.radians(a[0]); lon1 = math.radians(a[1])
    lat2 = math.radians(b[0]); lon2 = math.radians(b[1])
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
    return math.atan2(y, x)

def _turn_angle_deg(u, v, w):
    a = _bearing_rad(u, v); b = _bearing_rad(v, w)
    d = abs((b - a + math.pi) % (2*math.pi) - math.pi)
    return math.degrees(d)

def _route_turn_penalty_seconds(route_idx, coords, angle_thresh_deg=120.0, per_deg_penalty_s=0.6):
    """Sum soft penalties for sharp turns at internal nodes of the current route.
       No effect below threshold; linear penalty above.
       Returns seconds to be added to the objective."""
    if len(route_idx) < 3:
        return 0.0
    pen = 0.0
    for k in range(1, len(route_idx)-1):
        u, v, w = route_idx[k-1], route_idx[k], route_idx[k+1]
        ang = _turn_angle_deg(coords[u], coords[v], coords[w])
        if ang >= angle_thresh_deg:
            pen += (ang - angle_thresh_deg) * per_deg_penalty_s
    return pen


def feasible_sites_mask(
    start_idx: int,
    end_idx: Optional[int],
    site_idx_offset: int,
    M: List[List[int]],
    budget_s: int,
    open_end: bool,
    n_sites: int,
) -> List[bool]:
    #Return a boolean mask of length n_sites for feasibility prefilter.
    mask = [True] * n_sites
    for k in range(n_sites):
        idx = site_idx_offset + k
        to_k = M[start_idx][idx]
        if open_end:
            feas = (to_k <= budget_s)
        else:
            back = M[idx][end_idx if end_idx is not None else start_idx]
            feas = (to_k + back <= budget_s)
        mask[k] = bool(feas and to_k < 10**9)
    return mask

#------------------------------------------------------------------------------
# ROUTERS:

class HaversineRouter:
    def __init__(self, walk_speed_mps: float = DEFAULT_WALK_SPEED_MPS):
        self.v = max(0.5, float(walk_speed_mps))

    def time_matrix_seconds(self, coords: List[Tuple[float, float]]) -> List[List[int]]:
        """Return symmetric time matrix in seconds using haversine / v.
        coords: [(lat, lon), ...]
        """
        n = len(coords)
        mat = [[0]*n for _ in range(n)]
        for i in range(n):
            lat_i, lon_i = coords[i]
            for j in range(i+1, n):
                lat_j, lon_j = coords[j]
                d_m = haversine_m(lat_i, lon_i, lat_j, lon_j)
                t_s = int(round(d_m / self.v))
                mat[i][j] = t_s
                mat[j][i] = t_s
        return mat

class TimeMatrixRouter:
    """Interface: give it coords -> get an NxN seconds matrix."""
    def time_matrix_seconds(self, coords: List[Tuple[float, float]]) -> List[List[int]]:
        raise NotImplementedError

class OSRMRouter(TimeMatrixRouter):
    def __init__(self, base_url: str, max_coords_per_call: int = 140, workers: int = 12):
        if not base_url:
            raise ValueError("OSRM base_url required (e.g. http://localhost:5000)")
        self.base = base_url.rstrip("/")
        self.max_coords = int(max_coords_per_call)   # total coords per call (sources ∪ destinations)
        self.workers = int(workers)
        self.session = requests.Session()            # keep-alive
        self._hint_lock = Lock()
        self._hints = {}  # (round(lat,6), round(lon,6)) -> hint string

    def _coord_key(self, lat, lon):
        return (round(float(lat), 6), round(float(lon), 6))

    def _encode_coords(self, coords, used_idx):
        """Returns path coords string and aligned hints string (semicolon-separated)."""
        parts = []
        hints = []
        for i in used_idx:
            lat, lon = coords[i]
            parts.append(f"{lon:.6f},{lat:.6f}")
            with self._hint_lock:
                h = self._hints.get(self._coord_key(lat, lon), "")
            hints.append(h or "")
        return ";".join(parts), ";".join(hints)

    def _store_hints(self, coords, used_idx, js):
        # js['sources'] and js['destinations'] contain 'hint' for each listed index
        # We get hints for both; either is fine to cache.
        with self._hint_lock:
            for arr in ("sources", "destinations"):
                items = js.get(arr, [])
                # items align with the indices we requested for that role
                # but we encoded 'used' union; OSRM returns both arrays aligned to that union
                # In /table for GET with sources/destinations params, OSRM returns both arrays
                # aligned to the subset we sent. Safest: walk through 'items' in order.
                for k, i in enumerate(used_idx):
                    try:
                        hint = items[k].get("hint")
                    except Exception:
                        hint = None
                    if hint:
                        lat, lon = coords[i]
                        self._hints[self._coord_key(lat, lon)] = hint

    def _table_block(self, coords, src_idx, dst_idx):
        used = sorted(set(src_idx) | set(dst_idx))
        locs, hints = self._encode_coords(coords, used)
        url = f"{self.base}/table/v1/foot/{locs}"
        params = {
            "annotations": "duration",
            "sources":      ";".join(str(used.index(i)) for i in src_idx),
            "destinations": ";".join(str(used.index(i)) for i in dst_idx),
            "hints": hints,
        }
        r = self.session.get(url, params=params, timeout=60)
        # If URL too long, you can reduce max_coords_per_call
        r.raise_for_status()
        js = r.json()
        durs = js.get("durations")
        if durs is None:
            raise RuntimeError(f"OSRM returned no durations for block: {js}")
        # store hints back for future blocks
        self._store_hints(coords, used, js)
        return (src_idx, dst_idx, durs)

    def time_matrix_seconds(self, coords):
        n = len(coords)
        print(f"Calculating OSRM time matrix for {n} points using {self.workers} workers...")
        if n == 0:
            return []
        INF = 10**9
        M = [[INF]*n for _ in range(n)]

        # choose row/col block sizes so union ≤ max_coords
        b = max(1, self.max_coords // 2)
        row_blocks = [list(range(i, min(i+b, n))) for i in range(0, n, b)]
        col_blocks = [list(range(j, min(j+b, n))) for j in range(0, n, b)]

        tasks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            for rb in row_blocks:
                for cb in col_blocks:
                    # shrink if union too large (safety)
                    tmp_cb = cb[:]
                    while len(set(rb) | set(tmp_cb)) > self.max_coords and len(tmp_cb) > 1:
                        tmp_cb.pop()
                    tasks.append(ex.submit(self._table_block, coords, rb, tmp_cb))

            for fut in concurrent.futures.as_completed(tasks):
                src_idx, dst_idx, durs = fut.result()
                for ii, i in enumerate(src_idx):
                    for jj, j in enumerate(dst_idx):
                        v = durs[ii][jj]
                        if v is not None:
                            M[i][j] = int(round(v))

        for i in range(n):
            M[i][i] = 0
        
        print("M done")
        return M

#------------------------------------------------------------------------------
#Solver:

def simple_greedy_solver(
    start: Tuple[float, float],
    end: Optional[Tuple[float, float]],
    budget_s: int,
    sites: List[Site],
    M: List[List[int]],                 # <-- pass precomputed matrix
    site_idx_offset: int,               # usually 1 (coords[0] is start)
    end_index: Optional[int],           # index in coords[] or None
    roundtrip: bool,
    candidate_mask: Optional[List[bool]] = None,
    dwell_time_s: int = 0,   #300,                #temp zero!
    coords: Optional[List[Tuple[float,float]]] = None, 
    walk_speed_mps: float = 1.35,
    backtrack_angle_deg: float = 150.0,    # consider ≥ this as “backtrack-ish”
    backtrack_penalty_per_m: float = 0.15, # extra effective seconds per meter on near U-turns
    edge_reuse_penalty_s: float = 20.0,    # add if we reuse an (undirected) hop

) -> Tour:
    # Route indices are into the coords[] that M indexes.
    route: List[int] = [0]
    
    if end_index is not None:
        #Fixed end: must reach that endpoint
        route = [0, end_index]
    elif roundtrip:
        #Roundtrip:  must return to start
        route = [0, 0]
    else:
        #Open tour: no fixed endpoint  
        route = [0]

    # Candidate indices
    all_candidates = list(range(site_idx_offset, site_idx_offset + len(sites)))
    if candidate_mask:
        all_candidates = [site_idx_offset + i for i, keep in enumerate(candidate_mask) if keep]

    candidate_indices = set(all_candidates)
    
    
        # Keep a set of undirected hops already in the route to discourage ping-pong
    used_hops = set()  # {(min_idx,max_idx), ...}

    def route_time(current_route: List[int]) -> int:
        t = 0
        for i in range(len(current_route) - 1):
            t += M[current_route[i]][current_route[i+1]]
        return t

    travel_time = route_time(route)
    dwell_count =  0

    while candidate_indices:
        best_gain = 0.0
        best_insert = None
        #current_t = route_time(route)
        current_t = travel_time

        for c in list(candidate_indices): 
            best_for_c = None
            for pos in range(len(route) - 1 if (end_index is not None or roundtrip) else len(route)): #for each legal insertion point
                a = route[pos]
                #b = route[pos + 1] if (end_index is not None and pos + 1 < len(route)) else None
                b = route[pos + 1] if (pos + 1 < len(route)) else None             
                #base_added = M[a][c] + M[c][b] - M[a][b]
                base_added = M[a][c] + (M[c][b] if b is not None else 0) - (M[a][b] if b is not None else 0)
                if base_added >= 10**9: #skip if unreasonably large
                    continue

                # ---- Backtrack penalty (near U-turn at 'a') -------
                extra_s = 0.0
                if coords is not None and pos > 0:
                    u = route[pos - 1]
                    # angle between (u->a) and (a->c)
                    ang = _turn_angle_deg(coords[u], coords[a], coords[c])
                    if ang >= backtrack_angle_deg:
                        # approximate meters by time * v
                        dist_m = M[a][c] * walk_speed_mps
                        extra_s += backtrack_penalty_per_m * dist_m

                # ---- Edge reuse penalty (discourage using same hop again) ---------------------
                hop_ac = (min(a, c), max(a, c))
                if hop_ac in used_hops:
                    extra_s += edge_reuse_penalty_s
                if b is not None:
                    hop_cb = (min(c, b), max(c, b))
                    if hop_cb in used_hops:
                        extra_s += edge_reuse_penalty_s

                added_eff = base_added + int(round(extra_s))

                # total with dwell counted per *visited* stop
                #new_total = current_t + added_eff + dwell_time_s * (len(route) - 1)
                new_total = current_t + added_eff + dwell_time_s * (dwell_count + 1)
                if new_total > budget_s:
                    continue                #If exceeds time budget, we skip this insertion!

                score = sites[c - site_idx_offset].base_score
                gain = score / max(1, added_eff + dwell_time_s)

                if (best_for_c is None) or (gain > best_for_c[2]):  #Keep the insertion point that is best for candidate c!
                    best_for_c = (pos, added_eff, gain)

            if best_for_c:                       
                pos, added_eff, gain = best_for_c       #Keep global best among all c:s!
                if gain > best_gain:
                    best_gain = gain
                    best_insert = (c, pos, added_eff)

        if not best_insert:
            break

        c, pos, added_eff = best_insert
        # Insert and record the hops we just created
        a = route[pos]
        
        if pos + 1 < len(route):
            b = route[pos + 1]
            route.insert(pos + 1, c)
        else:
            b = None
            route.append(c)

        used_hops.add((min(a, c), max(a, c)))
        if b is not None:
            used_hops.add((min(c, b), max(c, b)))

        candidate_indices.remove(c)

        travel_time += added_eff
        dwell_count += 1
    
    travel_budget = max(0, budget_s - dwell_time_s * dwell_count)
    # smooth route order afterwards addition:
    route_sm = route[:]
    route_sm = two_opt_smooth(
        route_sm, M, coords, travel_budget,
        angle_thresh_deg=120.0, per_deg_penalty_s=0.6,
        lambda_turn=1.0, max_passes=2
    )
    route_sm = or_opt_1_smooth(
        route_sm, M, coords, travel_budget,
        angle_thresh_deg=120.0, per_deg_penalty_s=0.6,
        lambda_turn=1.0
    )
    route = route_sm

    legs = [M[route[i]][route[i+1]] for i in range(len(route) - 1)]

    #total_time = sum(legs)
    travel_time = sum(legs)
    total_time = travel_time + dwell_time_s * dwell_count

    visited_site_ids: List[str] = []
    contributions: Dict[str, float] = {}
    for idx in route:
        if idx >= site_idx_offset and (end_index is None or idx != end_index):
            site = sites[idx - site_idx_offset]
            visited_site_ids.append(site.id)
            contributions[site.id] = contributions.get(site.id, 0.0) + site.base_score

    return Tour(
        site_ids=visited_site_ids,
        leg_times_s=legs,
        stop_score=sum(contributions.values()),
        passby_score=0.0,
        contributions=contributions,
        total_time_s=total_time,
    )

#------------------------------------------------------------------------------
#POST-ROUTING SMOOTHHING HELPERS:
def _route_time_seconds(route_idx, M):
    t = 0
    for i in range(len(route_idx)-1):
        t += M[route_idx[i]][route_idx[i+1]]
    return t

def _route_objective(route_idx, M, coords, angle_thresh_deg, per_deg_penalty_s, lambda_turn=1.0):
    base = _route_time_seconds(route_idx, M)
    turn_pen = _route_turn_penalty_seconds(route_idx, coords, angle_thresh_deg, per_deg_penalty_s)
    return base + lambda_turn * turn_pen, base, turn_pen

def two_opt_smooth(route_idx, M, coords, budget_s,
                   angle_thresh_deg=120.0, per_deg_penalty_s=0.6, lambda_turn=1.0,
                   max_passes=2):
    """2-opt with smoothness; keeps endpoints fixed; respects budget on base time."""
    n = len(route_idx)
    if n < 4:
        return route_idx
    improved = True
    passes = 0
    best = route_idx[:]
    best_obj, best_base, _ = _route_objective(best, M, coords, angle_thresh_deg, per_deg_penalty_s, lambda_turn)

    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(1, n-2):          # keep 0 fixed
            for j in range(i+1, n-1):    # keep last fixed
                if j == i+1:
                    continue
                cand = best[:i] + best[i:j+1][::-1] + best[j+1:]
                base_time = _route_time_seconds(cand, M)
                if base_time > budget_s:   # don’t violate walking budget
                    continue
                obj, _, _ = _route_objective(cand, M, coords, angle_thresh_deg, per_deg_penalty_s, lambda_turn)
                if obj + 1e-6 < best_obj:
                    best = cand
                    best_obj = obj
                    best_base = base_time
                    improved = True
        # continue outer loop if improved
    return best

def or_opt_1_smooth(route_idx, M, coords, budget_s,
                    angle_thresh_deg=120.0, per_deg_penalty_s=0.6, lambda_turn=1.0):
    """Move a single node to a different place if it improves smoothness+time."""
    n = len(route_idx)
    if n < 4:
        return route_idx
    best = route_idx[:]
    best_obj, _, _ = _route_objective(best, M, coords, angle_thresh_deg, per_deg_penalty_s, lambda_turn)

    improved = True
    while improved:
        improved = False
        for i in range(1, n-1):  # movable node (not endpoints)
            node = best[i]
            rest = best[:i] + best[i+1:]
            for pos in range(1, len(rest)):
                cand = rest[:pos] + [node] + rest[pos:]
                base_time = _route_time_seconds(cand, M)
                if base_time > budget_s:
                    continue
                obj, _, _ = _route_objective(cand, M, coords, angle_thresh_deg, per_deg_penalty_s, lambda_turn)
                if obj + 1e-6 < best_obj:
                    best = cand
                    best_obj = obj
                    improved = True
                    break
            if improved:
                break
    return best

#------------------------------------------------------------------------------
# Map rendering

def render_map(
    start: Tuple[float, float],
    end: Optional[Tuple[float, float]],
    tour,                         # Tour
    site_lookup: Dict[str, "Site"],
    out_html: str,
    *,
    snap_base_url: Optional[str] = None,   # e.g. "http://localhost:5000"

    # NEW (optional, keeps backward-compat):
    all_pois: Optional[List["Place"]] = None,                 # nearby POIs (from cache or live)
    details_map: Optional[Dict[str, dict]] = None,            # xid -> OTM details
    wiki_views: Optional[Dict[str, dict]] = None,             # xid -> {project,title,views_365,score}
    radius_m: Optional[int] = None,                           # to draw a context circle (optional)
):
    import folium
    from folium import Icon, FeatureGroup, LayerControl, CircleMarker
    from folium.plugins import MarkerCluster

    m = folium.Map(location=[start[0], start[1]], zoom_start=14)

    # Start / End pins (unchanged)
    folium.Marker([start[0], start[1]], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    if end is not None:
        folium.Marker([end[0], end[1]], tooltip="End", icon=folium.Icon(color="red")).add_to(m)
    if radius_m and radius_m > 0:
        folium.Circle([start[0], start[1]], radius=radius_m, fill=True, opacity=0.25).add_to(m)

    # Build ordered stops: start -> sites -> (end?)
    stops: List[Tuple[float, float]] = [start]
    for sid in tour.site_ids:
        s = site_lookup[sid]
        stops.append((s.lat, s.lon))
    if end is not None:
        stops.append(end)

    # Draw path: snapped per leg if OSRM base URL provided (unchanged)
    total_dist_m = 0.0
    total_dur_s = 0.0                           #could set this to total time from the Tour if we want to later!
    if snap_base_url and len(stops) >= 2:
        for i in range(len(stops) - 1):
            a = stops[i]
            b = stops[i + 1]
            coords_latlon, dist_m, dur_s = osrm_route_leg(snap_base_url, a, b)
            total_dist_m += 0 if (dist_m != dist_m) else dist_m  # NaN check
            total_dur_s  += 0 if (dur_s  != dur_s)  else dur_s
            folium.PolyLine(coords_latlon, weight=5, opacity=0.9).add_to(m)
    else:
        coords = [[lat, lon] for (lat, lon) in stops]
        folium.PolyLine(coords, weight=5, opacity=0.8).add_to(m)

    # --- Tour Stops layer: always-visible BLUE pins, rich popup when possible ---
    tour_layer = FeatureGroup(name="Tour Stops (selected)", show=True).add_to(m)

    # Helper to extract an xid for a site (fallback to site_id if no xid attribute)
    def _site_xid(site_id: str, s: "Site") -> str:
        return getattr(s, "xid", None) or site_id

    for i, sid in enumerate(tour.site_ids, start=1):
        s = site_lookup[sid]
        # Try to build the rich popup (needs details/wiki); otherwise fall back to your old popup
        xid = _site_xid(sid, s)
        det = (details_map or {}).get(xid)
        wv  = (wiki_views  or {}).get(xid)

        if det or wv:
            # If your Site has kinds/raw_rate, use them; else show placeholders
            kinds = getattr(s, "kinds", []) or []
            raw_rate = getattr(s, "raw_rate", None)
            popup_html = _popup_html_for_place(
                name=s.name, xid=xid, lat=s.lat, lon=s.lon,
                origin_lat=start[0], origin_lon=start[1],
                kinds=kinds, raw_rate=raw_rate, det=det, wv=wv, score =s.base_score #SEND IN SCORE FOR THAT PLACE
            )
            # prepend numbering to tooltip to keep your numbering UX
            folium.Marker(
                [s.lat, s.lon],
                tooltip=f"{i}. {s.name}",
                popup=folium.Popup(popup_html, max_width=360),
                icon=Icon(icon="info-sign", color="blue"),
            ).add_to(tour_layer)
        else:
            # Backward-compatible simple popup (your original)
            popup = f"<b>{i}. {s.name}</b><br/>Score: {getattr(s, 'base_score', 0.0):.2f}<br/><small>{sid}</small>"
            folium.Marker([s.lat, s.lon], tooltip=f"{i}. {s.name}", popup=popup,
                          icon=Icon(icon="info-sign", color="blue")).add_to(tour_layer)

    # --- Nearby-but-not-selected POIs (optional) ---
    if all_pois:
        # Build a set of "selected" xids to split others out.
        selected_xids = set()
        for sid in tour.site_ids:
            selected_xids.add(_site_xid(sid, site_lookup[sid]))

        other_pois = [p for p in all_pois if getattr(p, "xid", None) not in selected_xids]

        # Dots layer (off by default, like explorer)
        dots = FeatureGroup(name="Nearby POIs (dots)", show=False).add_to(m)
        for p in other_pois:
            CircleMarker([p.lat, p.lon], radius=2.5, fill=True, fill_opacity=0.8, opacity=0).add_to(dots)

        # Clustered interactive markers (same behavior as explorer)
        cluster = MarkerCluster(
            name="Nearby POIs (interactive)",
            spiderfyOnMaxZoom=True,
            showCoverageOnHover=False
        ).add_to(m)

        for p in other_pois:
            xid = getattr(p, "xid", None)
            det = (details_map or {}).get(xid) if xid else None
            wv  = (wiki_views  or {}).get(xid) if xid else None
            popup_html = _popup_html_for_place(
                name=p.name, xid=xid, lat=p.lat, lon=p.lon,
                origin_lat=start[0], origin_lon=start[1],
                kinds=getattr(p, "kinds", []) or [],
                raw_rate=getattr(p, "raw_rate", None),  
                det=det, wv=wv, score = p.score                                 #SEND IN SCORE FOR THAT PLACE
            )   
            has_wiki = bool(wv and wv.get("project") and wv.get("title"))
            icon_color = "green" if has_wiki else "gray" #was blue

            folium.Marker(
                [p.lat, p.lon],
                popup=folium.Popup(popup_html, max_width=360),
                tooltip=p.name,
                icon=Icon(icon="info-sign", color=icon_color),
            ).add_to(cluster)

    LayerControl(collapsed=False).add_to(m)

    # Optional summary box (unchanged)
    try:
        if snap_base_url:
            km = total_dist_m / 1000.0
            mins = total_dur_s / 60.0
            folium.map.Marker(
                [start[0], start[1]],
                icon=folium.DivIcon(
                    html=(
                        "<div style='background:#fff;padding:6px 8px;border-radius:8px;border:1px solid #ccc;'>"
                        f"<b>Snapped walk</b>: ~{km:.1f} km, {mins:.0f} min</div>"
                    )
                ),
            ).add_to(m)
    except Exception:
        pass

    Path(out_html).parent.mkdir(parents=True, exist_ok=True)
    m.save(out_html)

#------------------------------------------------------------------------------
def build_sites(places: List[Place]) -> List[Site]:
    
    sites: List[Site] = []

    # NEW: load weights once
    # (We don't have args in scope here, so we’ll stash the weights in a module-global
    #  or pass them as a param. Easiest: make a module-global after parse_args() in main.)
    for p in places:

        # score = combined_place_score(p, wiki_views, w_otm=w_otm, w_wiki=w_wiki, rmin=rmin, rmax=rmax)
        score = p.score     #Just same as places!

        sites.append(
            Site(
                id=p.xid,
                name=p.name or "Unnamed",
                lat=p.lat,
                lon=p.lon,
                base_score=score,
                members=[(p.xid, 1.0)],
                #new:
                kinds=(getattr(p, "kinds", []) or []),   # pass tags through
                raw_rate=getattr(p, "raw_rate", None),   # pass OTM rate through
            )
        )
    print(len(sites))
    return sites

#------------------------------------------------------------------------------
# OSRM route helper (per-leg) producing GeoJSON line + stats:
def osrm_route_leg(base_url: str, a: Tuple[float, float], b: Tuple[float, float]):
    """
    Call /route/v1/foot for (a -> b).
    Returns (coords_latlon: List[List[float,float]], distance_m: float, duration_s: float)
    """
    import requests
    base = base_url.rstrip("/")
    lonlat = f"{a[1]:.6f},{a[0]:.6f};{b[1]:.6f},{b[0]:.6f}"
    url = f"{base}/route/v1/foot/{lonlat}"
    params = {
        "overview": "full",
        "geometries": "geojson",   # easy to draw with folium
        "continue_straight": "true"
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    js = r.json()
    routes = js.get("routes", [])
    if not routes:
        # Fallback to straight line if unroutable
        return [[a[0], a[1]], [b[0], b[1]]], float("nan"), float("nan")
    r0 = routes[0]
    geom = r0.get("geometry", {})
    coords_lonlat = geom.get("coordinates", [])  # [[lon,lat], ...]
    # convert to [[lat,lon], ...]
    coords_latlon = [[ll[1], ll[0]] for ll in coords_lonlat]
    dist = float(r0.get("distance", 0.0))
    dur  = float(r0.get("duration", 0.0))
    return coords_latlon, dist, dur


def osrm_route_leg_detailed(base_url: str, a: Tuple[float, float], b: Tuple[float, float]):
    """
    Call /route/v1/foot with steps=true to get detailed navigation info.
    Returns dict with:
    - coords_latlon: List of [lat, lon] coordinates
    - distance_m: total distance in meters
    - duration_s: total duration in seconds
    - steps: List of step dicts with {distance_m, duration_s, street_name, maneuver}
    - next_street_name: name of the first street segment (for navigation display)
    """
    import requests
    base = base_url.rstrip("/")
    lonlat = f"{a[1]:.6f},{a[0]:.6f};{b[1]:.6f},{b[0]:.6f}"
    url = f"{base}/route/v1/foot/{lonlat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",  # Get step-by-step instructions
        "continue_straight": "true"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        js = r.json()
        routes = js.get("routes", [])
        if not routes:
            return {
                "coords_latlon": [[a[0], a[1]], [b[0], b[1]]],
                "distance_m": float("nan"),
                "duration_s": float("nan"),
                "steps": [],
                "next_street_name": None,
            }
        r0 = routes[0]
        geom = r0.get("geometry", {})
        coords_lonlat = geom.get("coordinates", [])
        coords_latlon = [[ll[1], ll[0]] for ll in coords_lonlat]
        dist = float(r0.get("distance", 0.0))
        dur = float(r0.get("duration", 0.0))
        
        # Extract steps with maneuver types and modifiers (OSRM doesn't reliably provide street names)
        legs = r0.get("legs", [])
        steps = []
        if legs:
            leg0 = legs[0]
            leg_steps = leg0.get("steps", [])
            for step in leg_steps:
                step_dist = float(step.get("distance", 0.0))
                step_dur = float(step.get("duration", 0.0))
                maneuver = step.get("maneuver", {})
                maneuver_type = maneuver.get("type", "")
                maneuver_modifier = maneuver.get("modifier", "")  # e.g., "left", "right", "sharp left", "slight right"
                # Combine type and modifier for better turn detection
                # Format: "type:modifier" or just "type" if no modifier
                maneuver_str = maneuver_type
                if maneuver_modifier:
                    maneuver_str = f"{maneuver_type}:{maneuver_modifier}"
                steps.append({
                    "distance_m": step_dist,
                    "duration_s": step_dur,
                    "maneuver": maneuver_str,
                })
        
        return {
            "coords_latlon": coords_latlon,
            "distance_m": dist,
            "duration_s": dur,
            "steps": steps,
            "next_street_name": None,  # OSRM typically doesn't provide reliable street names
        }
    except Exception as e:
        print(f"[OSRM] detailed route failed: {e}")
        return {
            "coords_latlon": [[a[0], a[1]], [b[0], b[1]]],
            "distance_m": float("nan"),
            "duration_s": float("nan"),
            "steps": [],
            "next_street_name": None,
        }


#------------------------------------------------------------------------------
# CLI

def parse_args():
    ap = argparse.ArgumentParser(description="Spontaneous Walking Tour (prototype skeleton)")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)

    ap.add_argument("--time-min", type=int, required=True, help="Walking time budget in minutes")
    #ap.add_argument("--radius-m", type=int, default=2500)
    ap.add_argument("--radius-m", type=int, default=700)

    ap.add_argument("--roundtrip", type=int, default=1, help="1 = return to start, 0 = open end")
    ap.add_argument("--end-lat", type=float, default=None)
    ap.add_argument("--end-lon", type=float, default=None)

    ap.add_argument("--outdir", type=str, default=OUTDIR_DEFAULT)

    ap.add_argument("--walk-speed-mps", type=float, default=DEFAULT_WALK_SPEED_MPS,
                    help="Only for the fallback router in this step")

    ap.add_argument("--api-key", type=str, default=None)

    ap.add_argument("--router", type=str, default="offline",
                choices=["offline", "osrm", "valhalla", "haversine"],
                help="Walking time source: offline (OSMnx), osrm, valhalla, or haversine fallback")

    ap.add_argument("--router-url", type=str, default=None,
                    help="Base URL for OSRM, e.g. http://localhost:5000 or http://localhost:8002")

    # Offline (OSMnx) tuning
    ap.add_argument("--offline-network-radius-m", type=int, default=3500,
                    help="OSMnx graph radius around start (meters)")
    ap.add_argument("--offline-cache", type=str, default="out/osm_graph.gpkg",
                    help="Path to cache the OSMnx graph (optional)")
    
    ap.add_argument("--dwell-sec", type=int, default=180,  # 3 min realistic pause
                help="Assumed dwell/stop time per POI in seconds (set 0 to ignore)")
    ap.add_argument("--isochrone-frac", type=float, default=0.85,
                    help="Keep only POIs with t(start->poi)+t(poi->end_or_start) <= frac * budget")
    ap.add_argument("--score-gamma", type=float, default=1.5,
                    help="Score exponent for OTM rate: score = rate**gamma (diminishes cluster dominance)")
    
    ap.add_argument("--snap-path", type=int, default=1, help="1=draw real OSRM walking path, 0=straight lines")

    # in parse_args()
    ap.add_argument("--use-cache", action="store_true", help="Use local SQLite cache for POIs+Wiki")
    ap.add_argument("--cache-db", type=str, default="out/stockholm_wiki.db")

    #Cat weighing: NEEDS TO BE KEPT THE SAME IN EXPLORE AND TOUR
    ap.add_argument("--cat-w", action="append", default=[],
                    help="Repeatable key=value pairs to weight kinds. "
                         "Example: --cat-w gardens_and_parks=1.4 --cat-w cinemas=0.5")
    ap.add_argument("--cat-weights-json", type=str, default=None,
                    help="Path to a JSON file with {kind: weight, ...}.")



    return ap.parse_args()


def main():
    args = parse_args()

    # Origin / end handling
    start = (args.lat, args.lon)
    roundtrip = bool(args.roundtrip)
    end = None
    if not roundtrip:
        if args.end_lat is not None and args.end_lon is not None:
            end = (float(args.end_lat), float(args.end_lon))
        else:
            end = None  # open end

    scorer = Scorer(args)

    print("USING CACHE")
    places, wiki_views, details_map = load_cached_area(args.cache_db, args.lat, args.lon, args.radius_m, scorer)

    print("LOAD CACHED AREA DONE")

    sites = build_sites(places)

    site_lookup = {s.id: s for s in sites}

    print("BUILDING SITES DONE")

    # Router selection
    if args.router == "osrm":
        if not args.router_url:
            raise SystemExit("Please provide --router-url for OSRM, e.g. http://localhost:5000")
        router: TimeMatrixRouter = OSRMRouter(args.router_url)
    else:
        # haversine fallback
        router = HaversineRouter(walk_speed_mps=args.walk_speed_mps)

    # Solve (placeholder)
    budget_s = int(args.time_min * 60)

    # Build coords: [start] + sites + [end?]
    coords: List[Tuple[float, float]] = [start] + [(s.lat, s.lon) for s in sites]
    site_idx_offset = 1
    end_coord = start if (roundtrip and end is None) else end
    end_index = None
    if end_coord is not None:
        coords.append(end_coord)
        end_index = len(coords) - 1

    print("BEGINNING TO CALCULATE M")
    # Compute time matrix from chosen router
    M = router.time_matrix_seconds(coords)

    # Feasibility pre-filter
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
    # Solve using the prebuilt matrix and mask
    tour = simple_greedy_solver(
        start, end, budget_s, sites,
        M=M,
        site_idx_offset=site_idx_offset,
        end_index=end_index,
        roundtrip=roundtrip,
        candidate_mask=mask,
        dwell_time_s=args.dwell_sec,
        coords=coords,
        walk_speed_mps=args.walk_speed_mps,
        backtrack_angle_deg=150.0,
        backtrack_penalty_per_m=0.15,  # try 0.10..0.30
        edge_reuse_penalty_s=20.0,
    )

    

    # Output report
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "start": {"lat": start[0], "lon": start[1]},
        "end": ({"lat": end_coord[0], "lon": end_coord[1]} if end_coord is not None else None),
        "roundtrip": roundtrip,
        "time_budget_s": budget_s,
        "tour": {
            "site_ids": tour.site_ids,
            "leg_times_s": tour.leg_times_s,
            "stop_score": tour.stop_score,
            "passby_score": tour.passby_score,
            "total_time_s": tour.total_time_s,
            "contributions": tour.contributions,
        },
    }
    with open(outdir / f"tour_report_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Render map
    out_html = str(outdir / "tour.html")
    snap_url = args.router_url if (args.snap_path and args.router == "osrm") else None

    render_map(
        start, end_coord, tour, site_lookup, out_html,
        snap_base_url=snap_url,
        all_pois=places,
        details_map=details_map,
        wiki_views=wiki_views,
        radius_m=args.radius_m,)
    

    print(f"[OK] Wrote {out_html}  |  visited {len(tour.site_ids)} sites  |  score={tour.stop_score:.2f}")


if __name__ == "__main__":
    main()

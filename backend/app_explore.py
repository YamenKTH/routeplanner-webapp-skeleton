from __future__ import annotations
import argparse
import html
import json
import math
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterable
from urllib.parse import quote, urlparse, unquote
import unicodedata, re

import requests

#Scorer! 
from Scorer import Scorer


# .env support
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except Exception:
    pass

# -----------------------------
# Constants
# -----------------------------

OTM_BASE = "https://api.opentripmap.com/0.1/en/places"
WKV_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
WD_API  = "https://www.wikidata.org/wiki/Special:EntityData"
UA = {"User-Agent": "otm-wiki-views-cache/1.0 (+no PII)"}

# -----------------------------
# Data model
# -----------------------------

@dataclass
class Place:
    xid: str
    name: str
    lat: float
    lon: float
    kinds: List[str]
    raw_rate: float     #OTM RATING!
    score: float | None = None   # The actual score computed in Scorer. 

# -----------------------------
# Geo helper
# -----------------------------

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

# -----------------------------
# OpenTripMap client (live fetch)
# -----------------------------

class OpenTripMapClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OPENTRIPMAP_API_KEY is required")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(UA)

    def fetch_places(self, lat: float, lon: float, radius_m: int = 2500, *,
                     limit: Optional[int] = None, rate_min: int = 2,
                     kinds: str = (
                        "interesting_places,museums,historic,architecture,gardens_and_parks,"
                        "natural,urban_environment"   #view_points , art? cultural? other??????
                     )) -> List[Place]:
        page_size = 500
        to_fetch = float("inf") if limit is None else max(0, int(limit))
        places: List[Place] = []
        offset = 0
        while len(places) < to_fetch:
            fetch_n = page_size if limit is None else min(page_size, to_fetch - len(places))
            params = {
                "apikey": self.api_key,
                "radius": int(radius_m),
                "lon": float(lon),
                "lat": float(lat),
                "format": "json",
                "limit": int(fetch_n),
                "rate": int(rate_min),
                "offset": int(offset),
                "kinds": kinds,
            }
            r = self.session.get(f"{OTM_BASE}/radius", params=params, timeout=30)
            r.raise_for_status()
            items = r.json() or []
            for it in items:
                xid = it.get("xid") or it.get("id") or ""
                name = it.get("name") or "Unnamed"
                lat_i = it.get("point", {}).get("lat") or it.get("lat")
                lon_i = it.get("point", {}).get("lon") or it.get("lon")
                kinds_list = (it.get("kinds") or "").split(",")
                rate = float(it.get("rate", 1.0))
                if xid and lat_i is not None and lon_i is not None:
                    places.append(Place(xid=xid, name=name, lat=float(lat_i), lon=float(lon_i),
                                        kinds=kinds_list, raw_rate=rate))
            received = len(items)
            if received < fetch_n:
                break
            offset += received
        return places

    def fetch_details(self, xid: str) -> Dict:
        params = {"apikey": self.api_key}
        r = self.session.get(f"{OTM_BASE}/xid/{xid}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()


#DUPLICATE REMOVERS

def _normalize_name(name: str) -> str:
    return (name or "").strip().casefold()

""" def dedupe_pois(
    pois: List[Place],
    wiki_views: Dict[str, Dict],
    details_map: Dict[str, Dict],
    *,
    eps_m: int = 60,
) -> Tuple[List[Place], Dict[str, Dict], Dict[str, Dict]]:
    #Merge POIs that share the same normalized name and lie within eps_m meters.
    #Representative is chosen by: has Wikipedia → higher raw_rate → closer to centroid.
    #Returns (new_pois, new_wiki_views, new_details_map).
    #
    # group by normalized name
    buckets: Dict[str, List[Place]] = {}
    for p in pois:
        buckets.setdefault(_normalize_name(p.name), []).append(p)

    keep: List[Place] = []
    wv_new: Dict[str, Dict] = {}
    det_new: Dict[str, Dict] = {}

    def representative(cands: List[Place]) -> Place:
        if len(cands) == 1:
            return cands[0]
        # centroid
        clat = sum(p.lat for p in cands) / len(cands)
        clon = sum(p.lon for p in cands) / len(cands)
        # score each candidate
        def score(p: Place):
            has_wiki = 1 if wiki_views.get(p.xid) and wiki_views[p.xid].get("project") else 0
            return (
                has_wiki,
                float(p.raw_rate or 0.0),
                -haversine_m(clat, clon, p.lat, p.lon),
            )
        return sorted(cands, key=score, reverse=True)[0]

    for plist in buckets.values():
        # cluster by proximity using simple greedy O(n^2)
        unassigned = set(range(len(plist)))
        while unassigned:
            i = unassigned.pop()
            near = []
            for j in list(unassigned):
                if haversine_m(plist[i].lat, plist[i].lon, plist[j].lat, plist[j].lon) <= eps_m:
                    near.append(j)
            for j in near:
                unassigned.remove(j)
            cands = [plist[k] for k in [i] + near]
            rep = representative(cands)
            keep.append(rep)
            if rep.xid in wiki_views:
                wv_new[rep.xid] = wiki_views[rep.xid]
            if rep.xid in details_map:
                det_new[rep.xid] = details_map[rep.xid]

    return keep, wv_new, det_new """


_WS_RE = re.compile(r"\s+")
def _normalize_name(name: str) -> str:
    """
    Robust 'exact' name canonicalizer:
    - NFKC normalize (unifies composed/decomposed unicode)
    - convert NBSP to space, strip zero-width chars
    - collapse internal whitespace, trim ends
    - casefold (better than lower for unicode)
    """
    s = (name or "")
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u00A0", " ")      # NBSP
    s = s.replace("\u200B", "")       # zero-width space
    s = _WS_RE.sub(" ", s).strip()
    return s.casefold()

def dedupe_pois(
    pois: List[Place],
    wiki_views: Dict[str, Dict],
    details_map: Dict[str, Dict],
    *,
    eps_m: int = 60,
) -> Tuple[List[Place], Dict[str, Dict], Dict[str, Dict]]:
    """
    Merge POIs that share the same normalized name and are connected by
    <= eps_m proximity (transitive / single-linkage).
    Representative chosen by:
      1) has Wikipedia entry
      2) higher raw_rate
      3) closer to the cluster centroid
    """
    # group by robust-normalized name
    buckets: Dict[str, List[Place]] = {}
    for p in pois:
        buckets.setdefault(_normalize_name(p.name), []).append(p)

    keep: List[Place] = []
    wv_new: Dict[str, Dict] = {}
    det_new: Dict[str, Dict] = {}

    def representative(cands: List[Place]) -> Place:
        if len(cands) == 1:
            return cands[0]
        clat = sum(p.lat for p in cands) / len(cands)
        clon = sum(p.lon for p in cands) / len(cands)
        def score(p: Place):
            has_wiki = 1 if (wiki_views.get(p.xid) and wiki_views[p.xid].get("project")) else 0
            return (
                has_wiki,
                float(p.raw_rate or 0.0),
                -haversine_m(clat, clon, p.lat, p.lon),
            )
        return max(cands, key=score)

    # build connected components under distance<=eps_m in each same-name bucket
    for plist in buckets.values():
        n = len(plist)
        if n == 1:
            p = plist[0]
            keep.append(p)
            if p.xid in wiki_views: wv_new[p.xid] = wiki_views[p.xid]
            if p.xid in details_map: det_new[p.xid] = details_map[p.xid]
            continue

        visited = [False] * n
        for i in range(n):
            if visited[i]:
                continue
            comp = []
            stack = [i]
            visited[i] = True
            while stack:
                u = stack.pop()
                comp.append(u)
                pu = plist[u]
                for v in range(n):
                    if not visited[v]:
                        pv = plist[v]
                        if haversine_m(pu.lat, pu.lon, pv.lat, pv.lon) <= eps_m:
                            visited[v] = True
                            stack.append(v)

            cands = [plist[k] for k in comp]
            rep = representative(cands)
            keep.append(rep)
            if rep.xid in wiki_views: wv_new[rep.xid] = wiki_views[rep.xid]
            if rep.xid in details_map: det_new[rep.xid] = details_map[rep.xid]

    return keep, wv_new, det_new

# -----------------------------
# Wikipedia helpers (resolution + pageviews)
# -----------------------------

def _safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def _clean_title(t: str) -> str:
    t = unquote(t or "").strip()
    if t.startswith("/wiki/"):
        t = t[len("/wiki/"):]
    return t.replace(" ", "_")


def resolve_wiki_via_wikidata(qid: str, preferred_langs=("sv","en")) -> Optional[Dict]:
    try:
        r = requests.get(f"{WD_API}/{qid}.json", timeout=20, headers=UA)
        r.raise_for_status()
        data = r.json()
        entity = _safe_get(data, "entities", qid, default={})
        sitelinks = entity.get("sitelinks", {})
        for lang in preferred_langs:
            key = f"{lang}wiki"
            if key in sitelinks:
                title = sitelinks[key].get("title", "").replace(" ", "_")
                return {"project": f"{lang}.wikipedia.org", "title": title}
    except Exception:
        pass
    return None


def resolve_wiki_from_details(det: Dict) -> Optional[Dict]:
    w = det.get("wikipedia")
    if isinstance(w, str) and w:
        w = w.strip()
        if w.startswith("http://") or w.startswith("https://"):
            p = urlparse(w)
            host = (p.netloc or "").lower()
            path = p.path or ""
            if host.endswith(".wikipedia.org") and path:
                return {"project": host, "title": _clean_title(path)}
        elif ":" in w:
            lang, title = w.split(":", 1)
            if lang and title:
                return {"project": f"{lang}.wikipedia.org", "title": _clean_title(title)}

    wx = det.get("wikipedia_extracts") or {}
    lang = wx.get("lang")
    title = wx.get("title")
    url = wx.get("url")
    if url and (url.startswith("http://") or url.startswith("https://")):
        p = urlparse(url)
        host = (p.netloc or "").lower()
        path = p.path or ""
        if host.endswith(".wikipedia.org") and path:
            return {"project": host, "title": _clean_title(path)}
    if lang and title:
        return {"project": f"{lang}.wikipedia.org", "title": _clean_title(title)}

    qid = det.get("wikidata")
    if qid:
        wk = resolve_wiki_via_wikidata(qid, preferred_langs=("sv","en"))
        if wk:
            wk["title"] = _clean_title(wk["title"])
            return wk
    return None


def normalize_title_via_summary(project: str, title: str, *, debug: bool = False) -> str:
    url = f"https://{project}/api/rest_v1/page/summary/{quote(title, safe='')}"
    try:
        r = requests.get(url, timeout=15, headers={**UA, "accept": "application/json"})
        if debug:
            print("[wiki] summary", r.status_code, url)
        if r.status_code == 200:
            data = r.json() or {}
            t = (data.get("title") or title).replace(" ", "_")
            return t
    except Exception:
        if debug:
            print("[wiki] summary error", url)
    return title.replace(" ", "_")


def fetch_pageviews_365(project: str, title: str, *, debug: bool = False) -> int:
    norm_title = normalize_title_via_summary(project, title, debug=debug)
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=364)
    url = (
        f"{WKV_API}/{project}/all-access/all-agents/"
        f"{quote(norm_title, safe='')}/daily/{start:%Y%m%d}/{end:%Y%m%d}"
    )
    try:
        rr = requests.get(url, timeout=20, headers={**UA, "accept": "application/json"})
        if debug:
            print("[wiki] pageviews", rr.status_code, url)
        if rr.status_code == 404:
            return 0
        rr.raise_for_status()
        items = rr.json().get("items", [])
        return sum(int(i.get("views", 0)) for i in items)
    except Exception:
        if debug:
            print("[wiki] pageviews error", url)
        return 0

#------------------------------------------------------------------------------
# SQLite cache (schema + helpers)

DDL = {
    "poi": """
        CREATE TABLE IF NOT EXISTS poi (
            xid TEXT PRIMARY KEY,
            name TEXT,
            lat REAL,
            lon REAL,
            kinds TEXT,
            raw_rate REAL,
            created_ts TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_ts TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "poi_rtree": """
        CREATE TABLE IF NOT EXISTS poi_key (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            xid TEXT UNIQUE
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS poi_rtree USING rtree(
            id, minX, maxX, minY, maxY
        );
    """,
    "details": """
        CREATE TABLE IF NOT EXISTS details (
            xid TEXT PRIMARY KEY,
            json TEXT,
            updated_ts TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "wiki": """
        CREATE TABLE IF NOT EXISTS wiki (
            xid TEXT PRIMARY KEY,
            project TEXT,
            title TEXT,
            qid TEXT,
            updated_ts TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "pageviews": """
        CREATE TABLE IF NOT EXISTS pageviews (
            project TEXT,
            title   TEXT,
            as_of   TEXT,
            views_365 INTEGER,
            json_daily TEXT,
            updated_ts TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (project, title)
        );
    """,
    "idx": """
        CREATE INDEX IF NOT EXISTS idx_poi_name ON poi(name);
        CREATE INDEX IF NOT EXISTS idx_wiki_project_title ON wiki(project, title);
    """,
}


def db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def db_init(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    for sql in DDL.values():
        cur.executescript(sql)
    conn.commit()


def _ensure_poi_key(conn: sqlite3.Connection, xid: str) -> int:
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO poi_key(xid) VALUES (?)", (xid,))
    cur.execute("SELECT id FROM poi_key WHERE xid=?", (xid,))
    row = cur.fetchone()
    return int(row[0])


def upsert_poi(conn: sqlite3.Connection, p: Place) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO poi(xid,name,lat,lon,kinds,raw_rate)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(xid) DO UPDATE SET
            name=excluded.name,
            lat=excluded.lat,
            lon=excluded.lon,
            kinds=excluded.kinds,
            raw_rate=excluded.raw_rate,
            updated_ts=CURRENT_TIMESTAMP
        """,
        (p.xid, p.name, p.lat, p.lon, ",".join(p.kinds), float(p.raw_rate)),
    )
    pid = _ensure_poi_key(conn, p.xid)
    cur.execute("DELETE FROM poi_rtree WHERE id=?", (pid,))
    cur.execute("INSERT INTO poi_rtree(id,minX,maxX,minY,maxY) VALUES (?,?,?,?,?)",
                (pid, p.lon, p.lon, p.lat, p.lat))
    conn.commit()


def upsert_details(conn: sqlite3.Connection, xid: str, details_json: Dict) -> None:
    conn.execute(
        """
        INSERT INTO details(xid, json) VALUES(?,?)
        ON CONFLICT(xid) DO UPDATE SET json=excluded.json, updated_ts=CURRENT_TIMESTAMP
        """,
        (xid, json.dumps(details_json, ensure_ascii=False)),
    )
    conn.commit()


def upsert_wiki(conn: sqlite3.Connection, xid: str, project: Optional[str], title: Optional[str], qid: Optional[str]) -> None:
    conn.execute(
        """
        INSERT INTO wiki(xid, project, title, qid) VALUES(?,?,?,?)
        ON CONFLICT(xid) DO UPDATE SET project=excluded.project, title=excluded.title,
            qid=excluded.qid, updated_ts=CURRENT_TIMESTAMP
        """,
        (xid, project, title, qid),
    )
    conn.commit()


def upsert_pageviews(conn: sqlite3.Connection, project: str, title: str, views_365: int, json_daily: Optional[dict] = None) -> None:
    conn.execute(
        """
        INSERT INTO pageviews(project,title,as_of,views_365,json_daily)
        VALUES(?,?,?,?,?)
        ON CONFLICT(project,title) DO UPDATE SET
            as_of=excluded.as_of,
            views_365=excluded.views_365,
            json_daily=excluded.json_daily,
            updated_ts=CURRENT_TIMESTAMP
        """,
        (project, title, date.today().isoformat(), int(views_365),
         json.dumps(json_daily, ensure_ascii=False) if json_daily else None),
    )
    conn.commit()

#------------------------------------------------------------------------------
# Prefetch logic (tiling bbox)

def _tile_bbox(min_lat: float, min_lon: float, max_lat: float, max_lon: float, step_m: int) -> Iterable[Tuple[float,float]]:
    def deg_per_meter_lat():
        return 1.0 / 111_320.0
    lat_step = step_m * deg_per_meter_lat()
    lat = min_lat
    while lat <= max_lat:
        lon_step = step_m * deg_per_meter_lat() / max(math.cos(math.radians(lat)), 1e-6)
        lon = min_lon
        while lon <= max_lon:
            yield (lat, lon)
            lon += lon_step
        lat += lat_step


def prefetch_area(
    db_path: str,
    bbox: Tuple[float,float,float,float],
    grid_m: int,
    radius_m: int,
    otm_rate_min: int = 1,
    kinds: Optional[str] = None,
    sleep_otm_ms: int = 20,
    sleep_wiki_ms: int = 50,
    max_pois: Optional[int] = None,
) -> None:
    api_key = os.getenv("OPENTRIPMAP_API_KEY", "")
    client = OpenTripMapClient(api_key)

    conn = db_connect(db_path)
    db_init(conn)

    min_lat, min_lon, max_lat, max_lon = bbox
    kinds_str = kinds or (
        "interesting_places,museums,historic,architecture,gardens_and_parks,natural,urban_environment"
    )

    seen_xids: set[str] = set()
    total_new = 0

    for (lat, lon) in _tile_bbox(min_lat, min_lon, max_lat, max_lon, grid_m):
        try:
            places = client.fetch_places(lat, lon, radius_m, limit=None, rate_min=otm_rate_min, kinds=kinds_str)
        except Exception:
            places = []
        time.sleep(sleep_otm_ms / 1000.0)

        for p in places:
            if max_pois is not None and total_new >= max_pois:
                break
            if p.xid in seen_xids:
                continue
            seen_xids.add(p.xid)
            upsert_poi(conn, p)

            # details
            try:
                det = client.fetch_details(p.xid)
                upsert_details(conn, p.xid, det)
            except Exception:
                det = None
            time.sleep(sleep_otm_ms / 1000.0)

            # wiki resolution
            wk = resolve_wiki_from_details(det or {}) if det else None
            if wk:
                upsert_wiki(conn, p.xid, wk.get("project"), wk.get("title"), (det or {}).get("wikidata"))
                # pageviews
                try:
                    v = fetch_pageviews_365(wk["project"], wk["title"])
                except Exception:
                    v = 0
                upsert_pageviews(conn, wk["project"], wk["title"], v)
                time.sleep(sleep_wiki_ms / 1000.0)
            else:
                upsert_wiki(conn, p.xid, None, None, (det or {}).get("wikidata") if det else None)

            total_new += 1
        if max_pois is not None and total_new >= max_pois:
            break

    conn.close()

def _table_exists(cur, name: str) -> bool:
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,))
    return cur.fetchone() is not None


#------------------------------------------------------------------------------
# Get the actual places FOR EXPLORING AND APP_TOUR

def load_cached_area(db_path: str, center_lat: float, center_lon: float, radius_m: int, scorer: "Scorer | None" = None ) -> Tuple[List[Place], Dict[str, Dict], Dict[str, Dict]]:
    """Return (pois, wiki_views, details_map) from the local cache only."""
    conn = db_connect(db_path)
    cur = conn.cursor()

    deg_lat = radius_m / 111_320.0
    deg_lon = radius_m / (111_320.0 * max(math.cos(math.radians(center_lat)), 1e-6))
    minX = center_lon - deg_lon
    maxX = center_lon + deg_lon
    minY = center_lat - deg_lat
    maxY = center_lat + deg_lat

    cur.execute(
        """
        SELECT poi_key.xid, poi.name, poi.lat, poi.lon, poi.kinds, poi.raw_rate
        FROM poi_rtree r
        JOIN poi_key ON poi_key.id = r.id
        JOIN poi ON poi.xid = poi_key.xid
        WHERE r.minX <= ? AND r.maxX >= ? AND r.minY <= ? AND r.maxY >= ?
        """,
        (maxX, minX, maxY, minY),
    )
    raw = cur.fetchall()

    pois: List[Place] = []
    for xid, name, lat, lon, kinds, raw_rate in raw:
        if haversine_m(center_lat, center_lon, lat, lon) <= radius_m:
            pois.append(Place(xid=xid, name=name, lat=float(lat), lon=float(lon),
                              kinds=(kinds or "").split(","), raw_rate=float(raw_rate or 1.0)))

    # details for the found POIs
    details_map: Dict[str, Dict] = {}
    if pois:
        xids = [p.xid for p in pois]
        qmarks = ",".join(["?"] * len(xids))
        cur.execute(f"SELECT xid, json FROM details WHERE xid IN ({qmarks})", xids)
        for xid, j in cur.fetchall():
            try:
                details_map[xid] = json.loads(j)
            except Exception:
                details_map[xid] = {}

    # wiki + pageviews for the found POIs
    wiki_views: Dict[str, Dict] = {}
    if pois:
        xids = [p.xid for p in pois]
        qmarks = ",".join(["?"] * len(xids))

        #Using effective views:
        if _table_exists(cur, "effective_views"):
            cur.execute(
                f"""
                SELECT w.xid, w.project, w.title,
                    COALESCE(ev.effective_views, pv.views_365, 0) AS views_365
                FROM wiki w
                LEFT JOIN effective_views ev ON ev.xid = w.xid
                LEFT JOIN pageviews pv ON pv.project = w.project AND pv.title = w.title
                WHERE w.xid IN ({qmarks})
                """,
                xids,
            )
        else:
            #Using uncleaned views:
            print("Have not cleaned data yet!")
            cur.execute(
                f"""
                SELECT w.xid, w.project, w.title,
                    COALESCE(pv.views_365, 0) AS views_365
                FROM wiki w
                LEFT JOIN pageviews pv ON pv.project = w.project AND pv.title = w.title
                WHERE w.xid IN ({qmarks})
                """,
                xids,
            )

        for xid, project, title, views_365 in cur.fetchall():
            if project and title:
                v = int(views_365 or 0)
                entry = {
                    "project": project,
                    "title": title,
                    "views_365": v,
                }
                wiki_views[xid] = entry 

    #only addition to remove duplicates:
    if pois:
        pois, wiki_views, details_map = dedupe_pois(
            pois, wiki_views, details_map, eps_m=int(250)
        )

    if scorer:      #score the places!
        for p in pois:
            p.score = scorer.score_place(p, wiki_views.get(p.xid))
    else: 
        print("DID NOT PROVIDE SCORER")
    conn.close()
    return pois, wiki_views, details_map

#------------------------------------------------------------------------------
# Map rendering:


def save_poi_explorer_map(
    origin_lat: float,
    origin_lon: float,
    pois: List[Place],
    radius_m: int,
    details: Optional[Dict[str, Dict]] = None,
    *,
    wiki_views: Optional[Dict[str, Dict]] = None,
    out_html: str = "out/poi_explorer.html",
):
    import folium
    from folium import Icon, FeatureGroup, LayerControl, CircleMarker
    from folium.plugins import MarkerCluster

    m = folium.Map(location=[origin_lat, origin_lon], zoom_start=14)
    folium.Marker([origin_lat, origin_lon], tooltip="You are here").add_to(m)
    folium.Circle([origin_lat, origin_lon], radius=radius_m, fill=True, opacity=0.3).add_to(m)

    dots = FeatureGroup(name="All POIs (dots)").add_to(m)
    for p in pois:
        CircleMarker([p.lat, p.lon], radius=2.5, fill=True, fill_opacity=0.8, opacity=0).add_to(dots)

    cluster = MarkerCluster(name="Places", spiderfyOnMaxZoom=True, showCoverageOnHover=False).add_to(m)

    for p in pois:
        d = haversine_m(origin_lat, origin_lon, p.lat, p.lon)
        det = (details or {}).get(p.xid, {})
        kinds = ", ".join([k for k in p.kinds[:6]])
        addr = det.get("address", {}) if isinstance(det, dict) else {}
        addr_line = ", ".join(filter(None, [addr.get("house_number"), addr.get("road"), addr.get("city")]))
        wiki_extract = det.get("wikipedia_extracts", {}).get("text") if isinstance(det, dict) else None
        if wiki_extract and len(wiki_extract) > 280:
            wiki_extract = wiki_extract[:280] + "…"
        url = det.get("otm") or det.get("url") or f"https://opentripmap.com/en/card?xid={p.xid}"

        score = p.score
        if score is None:
            score =0

        wv = (wiki_views or {}).get(p.xid)
        if wv and wv.get("project") and wv.get("title"):
            wp_url = f"https://{wv['project']}/wiki/{wv['title']}"
            wiki_line = (
                f"📖 Wikipedia views (365d): <b>{wv['views_365']:,}</b> "
                f"&nbsp;|&nbsp; Score: <b>{score}</b> "
                f"&nbsp;•&nbsp; <a target='_blank' href='{html.escape(wp_url)}'>Open article</a>"
            )
            icon_color = "green"
        else:
            wiki_line = ""
            icon_color = "blue"

        html_popup = f"""
        <b>{html.escape(p.name or 'Unnamed')}</b><br/>
        OTM rate: {p.raw_rate} &nbsp;•&nbsp; Distance: {int(d)} m<br/>
        <small>{html.escape(kinds)}</small><br/>
        {html.escape(addr_line) if addr_line else ''}
        <div style='margin-top:6px'>{html.escape(wiki_extract) if wiki_extract else ''}</div>
        <div style='margin-top:6px'>{wiki_line}</div>
        <div style='margin-top:6px'><a target='_blank' href='{html.escape(url)}'>Open in OpenTripMap</a></div>
        """

        marker = folium.Marker(
            [p.lat, p.lon],
            popup=folium.Popup(html_popup, max_width=360),
            tooltip=p.name,
            icon=Icon(icon="info-sign", color=icon_color),
        )
        marker.add_to(cluster)

    LayerControl(collapsed=False).add_to(m)
    Path(out_html).parent.mkdir(parents=True, exist_ok=True)
    m.save(out_html)

#------------------------------------------------------------------------------
# CLI

def build_parser():
    ap = argparse.ArgumentParser(description="POI explorer with optional offline cache (SQLite)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # Explore (existing behavior + --use-cache)
    ex = sub.add_parser("explore", help="Render a Folium map of POIs (live or from cache)")
    ex.add_argument("--lat", type=float, required=True)
    ex.add_argument("--lon", type=float, required=True)
    ex.add_argument("--radius-m", type=int, default=2500)
    ex.add_argument("--api-key", type=str, default=None, help="OpenTripMap API key (overrides env if set)")
    ex.add_argument("--outdir", type=str, default="out")
    
    #ex.add_argument("--limit-pois", type=int, default=None, help="Max POIs to fetch from OpenTripMap (live mode)")
    #ex.add_argument("--otm-rate-min", type=int, default=2, help="Min OTM rate to include (1..3) (live mode)")
    #ex.add_argument("--details", type=int, default=0, help="Fetch OTM details for first N POIs (live mode)")
    ex.add_argument("--wiki-max", type=int, default=200, help="Max POIs to attempt Wikipedia view lookup for (live mode)")
    ex.add_argument("--wiki-skip-if-nonexistent", action="store_true",
                    help="Skip view lookups if no Wikipedia link is resolved (live mode)")
    ex.add_argument("--wiki-sleep-ms", type=int, default=50, help="Sleep between wiki requests (ms) (live mode)")
    ex.add_argument("--wiki-debug", action="store_true", help="Print debug info (live mode)")
    #ex.add_argument("--use-cache", action="store_true", help="Use local SQLite cache instead of live calls")
    ex.add_argument("--cache-db", type=str, default="out/stockholm_wiki.db")
    ex.add_argument("--dedupe", action="store_true",
                help="Collapse near-duplicate POIs by name within eps")
    ex.add_argument("--dedupe-eps-m", type=int, default=60,
                help="Max distance (meters) to consider duplicates")

    #CATEGORIES:
    ex.add_argument("--cat-w", action="append", default=[],
                    help="Repeatable key=value pairs to weight kinds. "
                         "Example: --cat-w gardens_and_parks=1.4 --cat-w cinemas=0.5")
    ex.add_argument("--cat-weights-json", type=str, default=None,
                    help="Path to a JSON file with {kind: weight, ...}.")
    

    # Cache prefetch
    pre = sub.add_parser("cache-prefetch", help="Crawl a bbox and store POIs + Wikipedia into SQLite cache")
    pre.add_argument("--bbox", type=str, required=True,
                     help="minLat,minLon,maxLat,maxLon (e.g., 59.15,17.60,59.50,18.30)")
    pre.add_argument("--grid-m", type=int, default=800, help="grid spacing in meters")
    pre.add_argument("--radius-m", type=int, default=1200, help="OTM /radius per grid center")
    pre.add_argument("--otm-rate-min", type=int, default=2, help="1..3 (lower=more places)")
    pre.add_argument("--kinds", type=str, default=None, help="OTM kinds CSV (optional)")
    pre.add_argument("--db", type=str, default="out/stockholm_wiki.db")
    pre.add_argument("--sleep-otm-ms", type=int, default=20)
    pre.add_argument("--sleep-wiki-ms", type=int, default=50)
    pre.add_argument("--max-pois", type=int, default=None, help="hard cap (optional)")

    return ap

# -----------------------------
# Main
# -----------------------------

def main():
    ap = build_parser()
    args = ap.parse_args()

    if args.cmd == "cache-prefetch":
        bbox = tuple(float(x) for x in args.bbox.split(","))
        if len(bbox) != 4:
            raise SystemExit("--bbox must be minLat,minLon,maxLat,maxLon")
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        prefetch_area(
            db_path=args.db,
            bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
            grid_m=int(args.grid_m),
            radius_m=int(args.radius_m),
            otm_rate_min=int(args.otm_rate_min),
            kinds=args.kinds,
            sleep_otm_ms=int(args.sleep_otm_ms),
            sleep_wiki_ms=int(args.sleep_wiki_ms),
            max_pois=int(args.max_pois) if args.max_pois is not None else None,
        )
        print(f"[OK] Prefetch complete → {args.db}")
        return

    # Explore mode
    assert args.cmd == "explore"
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    #CREATE THE SCORER:
    scorer = Scorer(args)

    #changed suich that we need to use the DB. probably simplest way (so we always use cache!)
    pois, wiki_views, details_map = load_cached_area(args.cache_db, args.lat, args.lon, args.radius_m, scorer)

    # Save JSON dump (POIs only; unchanged)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    with open(outdir / f"pois_{ts}.json", "w", encoding="utf-8") as f:
        json.dump([p.__dict__ for p in pois], f, indent=2)

    # Save interactive map
    save_poi_explorer_map(
        args.lat, args.lon, pois, args.radius_m,
        details_map, wiki_views=wiki_views,
        out_html=str(outdir / "poi_explorer.html"),
    )

    print(f"[OK] POI explorer saved to {outdir / 'poi_explorer.html'} with {len(pois)} markers")


if __name__ == "__main__":
    main()

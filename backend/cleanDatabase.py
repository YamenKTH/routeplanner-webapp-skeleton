#!/usr/bin/env python3
import argparse
import sqlite3
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path
import math
import html
import statistics

# Optional dependency: folium
try:
    import folium
    from folium import Icon
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False


# -----------------------------
# Helpers
# -----------------------------
def wiki_url(project: str | None, title: str | None) -> str | None:
    if not project or not title:
        return None
    host = project if project.endswith(".org") else f"{project}.org"
    slug = urllib.parse.quote(title.replace(" ", "_"))
    return f"https://{host}/wiki/{slug}"

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def deg_lon_for_radius(center_lat, radius_m):
    return radius_m / (111_320.0 * max(math.cos(math.radians(center_lat)), 1e-6))


# -----------------------------
# Schema bootstrap (idempotent)
# -----------------------------
BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS review_decisions (
  xid TEXT PRIMARY KEY,
  decision TEXT CHECK (decision IN ('keep','downweight','remove')),
  multiplier REAL,
  override_views INTEGER,
  notes TEXT,
  decided_ts TEXT
);
CREATE INDEX IF NOT EXISTS idx_review_decisions_decided_ts ON review_decisions(decided_ts);

CREATE TABLE IF NOT EXISTS effective_views (
  xid TEXT PRIMARY KEY,
  project TEXT,
  title TEXT,
  original_views INTEGER,
  multiplier REAL,
  effective_views INTEGER,
  updated_ts TEXT
);
"""

def bootstrap(conn: sqlite3.Connection) -> None:
    conn.executescript(BOOTSTRAP_SQL)
    conn.commit()


# -----------------------------
# Decisions + rebuild
# -----------------------------
def upsert_decision(cur, xid: str, decision: str,
                    multiplier: float | None, override_views: int | None, notes: str | None):
    if decision == "remove":
        multiplier = 0.0
        override_views = 0
    cur.execute("""
        INSERT INTO review_decisions(xid,decision,multiplier,override_views,notes,decided_ts)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(xid) DO UPDATE SET
          decision=excluded.decision,
          multiplier=excluded.multiplier,
          override_views=excluded.override_views,
          notes=excluded.notes,
          decided_ts=excluded.decided_ts
    """, (xid, decision, multiplier, override_views, notes, datetime.utcnow().isoformat(" ")))

def rebuild_effective_views(cur):
    # clear & rebuild from wiki + pageviews + decisions
    cur.execute("DELETE FROM effective_views")
    cur.execute("""
        INSERT INTO effective_views(xid, project, title, original_views, multiplier, effective_views, updated_ts)
        SELECT w.xid, w.project, w.title,
               COALESCE(pv.views_365, 0) AS original_views,
               CASE
                 WHEN d.decision='remove' THEN 0.0
                 WHEN d.multiplier IS NOT NULL THEN d.multiplier
                 ELSE 1.0
               END AS multiplier,
               CASE
                 WHEN d.decision='remove' THEN 0
                 WHEN d.override_views IS NOT NULL THEN d.override_views
                 WHEN d.multiplier IS NOT NULL THEN CAST(ROUND(COALESCE(pv.views_365,0) * d.multiplier) AS INTEGER)
                 ELSE COALESCE(pv.views_365,0)
               END AS effective_views,
               CURRENT_TIMESTAMP
        FROM wiki w
        JOIN poi p ON p.xid = w.xid
        LEFT JOIN pageviews pv ON pv.project=w.project AND pv.title=w.title
        LEFT JOIN review_decisions d ON d.xid=w.xid
        WHERE w.project IS NOT NULL AND w.title IS NOT NULL
    """)


# -----------------------------
# Nearby map rendering (optional)
# -----------------------------
def render_nearby_map(
    conn: sqlite3.Connection,
    center_xid: str,
    center_lat: float,
    center_lon: float,
    radius_m: int,
    out_html: Path
) -> None:
    if not HAS_FOLIUM:
        return

    cur = conn.cursor()
    tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    near_rows = []

    if {"poi_rtree","poi_key","poi"}.issubset(tables):
        deg_lat = radius_m / 111_320.0
        deg_lon = deg_lon_for_radius(center_lat, radius_m)
        minX = center_lon - deg_lon; maxX = center_lon + deg_lon
        minY = center_lat - deg_lat; maxY = center_lat + deg_lat
        cur.execute("""
            SELECT poi_key.xid, poi.name, poi.lat, poi.lon, poi.kinds, poi.raw_rate
            FROM poi_rtree r
            JOIN poi_key ON poi_key.id = r.id
            JOIN poi ON poi.xid = poi_key.xid
            WHERE r.minX <= ? AND r.maxX >= ? AND r.minY <= ? AND r.maxY >= ?
        """, (maxX, minX, maxY, minY))
        for xid, name, lat, lon, kinds, raw_rate in cur.fetchall():
            if haversine_m(center_lat, center_lon, lat, lon) <= radius_m:
                near_rows.append((xid, name, lat, lon, kinds, raw_rate))
    else:
        cur.execute("SELECT xid, name, lat, lon, kinds, raw_rate FROM poi")
        for xid, name, lat, lon, kinds, raw_rate in cur.fetchall():
            if haversine_m(center_lat, center_lon, lat, lon) <= radius_m:
                near_rows.append((xid, name, lat, lon, kinds, raw_rate))

    wiki_map = {}
    if near_rows and "wiki" in tables:
        ids = [x[0] for x in near_rows]
        q = ",".join("?"*len(ids))
        cur.execute(f"""
          SELECT w.xid, w.project, w.title, pv.views_365
          FROM wiki w
          LEFT JOIN pageviews pv ON pv.project=w.project AND pv.title=w.title
          WHERE w.xid IN ({q})
        """, ids)
        for xid, project, title, v in cur.fetchall():
            wiki_map[xid] = {"project": project, "title": title, "views_365": int(v or 0)}

    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
    folium.Circle([center_lat, center_lon], radius=radius_m, color="blue", fill=True, opacity=0.15).add_to(m)

    for xid, name, lat, lon, kinds, raw_rate in near_rows:
        klist = (kinds or "").split(",") if isinstance(kinds, str) else []
        w = wiki_map.get(xid)
        wp = wiki_url(w.get("project") if w else None, w.get("title") if w else None) if w else None
        views = (w or {}).get("views_365", 0)
        is_center = (xid == center_xid)
        icon_color = "red" if is_center else ("green" if w and w.get("title") else "blue")
        popup = f"<b>{html.escape(name or 'Unnamed')}</b><br/>xid: {html.escape(xid)}<br/>"
        popup += f"OTM rate: {raw_rate} &nbsp;•&nbsp; Views(365d): <b>{views:,}</b><br/>"
        if klist:
            popup += f"<small>{html.escape(', '.join(klist[:6]))}</small><br/>"
        if wp:
            popup += f"<a target='_blank' href='{html.escape(wp)}'>Open Wikipedia</a>"
        folium.Marker([lat, lon], tooltip=name, icon=Icon(icon="info-sign", color=icon_color),
                      popup=folium.Popup(popup, max_width=360)).add_to(m)

    out_html.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out_html))


# -----------------------------
# Candidate selection (top percentile)
# -----------------------------
def fetch_all_candidates(cur):
    """
    Returns list of dicts with xid, project, title, views_365, poi_name, poi_kinds, lat, lon.
    Filters to rows that have a wiki project+title and a POI row.
    """
    sql = """
    SELECT w.xid, w.project, w.title,
           COALESCE(pv.views_365, 0) AS views_365,
           p.name  AS poi_name,
           p.kinds AS poi_kinds,
           p.lat, p.lon
    FROM wiki w
    JOIN poi p ON p.xid = w.xid
    LEFT JOIN pageviews pv ON pv.project = w.project AND pv.title = w.title
    WHERE w.project IS NOT NULL AND w.title IS NOT NULL
    """
    rows = cur.execute(sql).fetchall()
    out = []
    for xid, project, title, v, poi_name, poi_kinds, lat, lon in rows:
        out.append({
            "xid": xid, "project": project, "title": title,
            "views_365": int(v or 0),
            "poi_name": poi_name, "poi_kinds": poi_kinds,
            "lat": lat, "lon": lon
        })
    return out

def percentile_threshold(values, p: float) -> int:
    """
    p in (0,1]. For example p=0.99 means keep top 1% (threshold at 99th percentile).
    Returns an integer threshold (views) at/above which items are "in the top p".
    """
    if not values:
        return 0
    if p <= 0:  # all
        return 0
    if p >= 1:
        return max(values)
    sorted_vals = sorted(values)
    # nearest-rank method
    k = max(1, int(math.ceil(p * len(sorted_vals))))
    return sorted_vals[k - 1]


# -----------------------------
# CLI + main
# -----------------------------
def main():
    ap = argparse.ArgumentParser(description="One-file reviewer: pick top percentile by Wikipedia 365d views, review, and rebuild.")
    ap.add_argument("--db", required=True, help="Path to SQLite DB")
    ap.add_argument("--percentile", type=float, default=0.99, help="e.g., 0.99 = top 1%% by views")
    ap.add_argument("--min-views", type=int, default=0, help="ignore candidates below this absolute views threshold")
    ap.add_argument("--limit", type=int, default=None, help="cap how many to review this run (after filtering)")
    ap.add_argument("--offset", type=int, default=0, help="skip N after filtering")
    ap.add_argument("--open", action="store_true", help="Also open the Wikipedia page in a browser tab")
    ap.add_argument("--open-map", action="store_true", help="Open generated HTML map (requires folium)")
    ap.add_argument("--radius-m", type=int, default=300, help="Map radius around candidate")
    ap.add_argument("--maps-outdir", type=str, default="out/review_maps", help="Folder for generated maps")
    ap.add_argument("--auto-rebuild", action="store_true", help="Rebuild effective_views automatically at the end")
    args = ap.parse_args()

    db_path = args.db
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Make sure schema is present
    bootstrap(conn)

    # Pull all potential candidates
    all_rows = fetch_all_candidates(cur)
    if not all_rows:
        print("No candidates found (no wiki/pageviews?).")
        return

    # Compute percentile threshold
    views = [r["views_365"] for r in all_rows if r["views_365"] is not None]
    thr = max(args.min_views, percentile_threshold(views, args.percentile))
    # Keep top percentile (>= threshold), then sort by views desc
    pool = [r for r in all_rows if r["views_365"] >= thr and r["views_365"] >= args.min_views]
    pool.sort(key=lambda r: r["views_365"], reverse=True)

    # page with offset/limit
    start = max(0, int(args.offset))
    end = len(pool) if args.limit is None else min(len(pool), start + int(args.limit))
    rows = pool[start:end]

    if not rows:
        print("Nothing to review for the given filters (try lowering --percentile or --min-views).")
        return

    print(f"Loaded {len(rows)} candidates (threshold={thr:,} views). Controls: [k]eep, [d]ownweight, [r]emove, [s]kip, [q]uit\n")

    for r in rows:
        xid = r["xid"]; project = r["project"]; title = r["title"]
        views_365 = r["views_365"]; poi_name = r["poi_name"]; poi_kinds = r["poi_kinds"]
        lat = r["lat"]; lon = r["lon"]

        url = wiki_url(project, title)
        header = f"{title} — {views_365:,} views — POI: {poi_name or '—'}"
        print("=" * len(header))
        print(header)
        print(f"xid={xid}")
        if url:
            print(url)

        # Show previous decision if any
        prev = cur.execute("SELECT decision, multiplier, override_views, notes FROM review_decisions WHERE xid=?",(xid,)).fetchone()
        if prev:
            print(f"Previous decision: {prev[0]}  multiplier={prev[1]}  override={prev[2]}  notes={prev[3]}")

        # Map
        map_file = None
        if HAS_FOLIUM and lat is not None and lon is not None:
            map_file = Path(args.maps_outdir) / f"{xid}.html"
            render_nearby_map(conn, xid, float(lat), float(lon), int(args.radius_m), map_file)
            if args.open_map:
                try:
                    webbrowser.open_new_tab(map_file.resolve().as_uri())
                except Exception:
                    pass

        # Article
        if args.open and url:
            try:
                webbrowser.open_new_tab(url)
            except Exception:
                pass

        # Decide
        while True:
            cmd = input("[k]eep, [d]ownweight, [r]emove, [s]kip, [q]uit > ").strip().lower()
            if cmd == "k":
                upsert_decision(cur, xid, "keep", 1.0, None, None)
                conn.commit()
                print("✓ kept")
                break
            elif cmd == "d":
                m = input("  multiplier 0.0–1.0 (default 0.5): ").strip()
                try:
                    multiplier = float(m) if m else 0.5
                except Exception:
                    multiplier = 0.5
                o = input("  override views (int, optional): ").strip()
                override = int(o) if o else None
                n = input("  notes (optional): ").strip() or None
                upsert_decision(cur, xid, "downweight", multiplier, override, n)
                conn.commit()
                print(f"✓ downweighted (multiplier={multiplier}, override={override})")
                break
            elif cmd == "r":
                n = input("  notes (optional): ").strip() or None
                upsert_decision(cur, xid, "remove", 0.0, 0, n)
                conn.commit()
                print("✓ removed")
                break
            elif cmd == "s":
                print("→ skipped")
                break
            elif cmd == "q":
                print("Exiting.")
                if args.auto_rebuild:
                    print("Rebuilding effective_views...")
                    rebuild_effective_views(cur)
                    conn.commit()
                    print("✅ effective_views rebuilt.")
                conn.close()
                return
            else:
                print("  Unknown command.")

    # End-of-batch rebuild?
    if args.auto_rebuild:
        print("\nRebuilding effective_views...")
        rebuild_effective_views(cur)
        conn.commit()
        print("✅ effective_views rebuilt.")
    else:
        ans = input("\nRebuild effective_views now? [y/N] ").strip().lower()
        if ans == "y":
            rebuild_effective_views(cur)
            conn.commit()
            print("✅ effective_views rebuilt.")

    conn.close()


if __name__ == "__main__":
    main()
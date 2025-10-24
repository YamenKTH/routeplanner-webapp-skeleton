import json

#perhaps send in a user later? 

class Scorer:
    # single source of truth for defaults
    DEFAULT_CAT_WEIGHTS = {             #here we can change the defaults!
        "gardens_and_parks": 2,
        "natural": 1.25,
        "view_points": 1.2,
        "historic": 1.2,
        "museums": 1.1,
        "architecture": 1.05,
        "urban_environment": 0.3,
        "theatres_and_entertainments": 0.2,
        "cinemas": 0.1,
        "railway_stations": 0.3,
    }

    def __init__(self, args=None, *, cat_weights=None):
        """
        If args is provided, read:
          - args.cat_weights_json (optional)
          - args.cat_w (repeatable key=value)
        Otherwise, use DEFAULT_CAT_WEIGHTS or explicit cat_weights.
        """
        # start from defaults
        w = dict(self.DEFAULT_CAT_WEIGHTS)

        # allow explicit dict override (rarely needed if you pass args)
        if cat_weights:
            w.update(cat_weights)

        # interpret CLI args if present
        if args is not None:
            # JSON file of weights
            path = getattr(args, "cat_weights_json", None)
            if path:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f) or {}
                        if isinstance(data, dict):
                            w.update(data)
                except Exception as e:
                    print(f"[WARN] Failed to read --cat-weights-json: {e}")

            # repeated --cat-w key=value
            for kv in (getattr(args, "cat_w", []) or []):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    try:
                        w[k.strip()] = float(v)
                    except Exception:
                        print(f"[WARN] Bad --cat-w '{kv}' (expected key=float). Ignored.")
                else:
                    print(f"[WARN] Bad --cat-w '{kv}' (expected key=value). Ignored.")

        self.cat_weights = w

    # --- scoring logic (tour-like: views × category weight) ---
    def _cat_weight(self, kinds):
        aliases = {
            "theatres": "theatres_and_entertainments",
            "parks": "gardens_and_parks",
            "park": "gardens_and_parks",
            "viewpoint": "view_points",
            "viewpoints": "view_points",
        }
        best = 1.0
        for k in (kinds or []):
            k = str(k).strip()
            if k in self.cat_weights:
                best = self.cat_weights[k]
            elif "." in k:
                tail = k.split(".")[-1]
                if tail in self.cat_weights:
                    best = self.cat_weights[tail]
            if k in aliases and aliases[k] in self.cat_weights:
                best = self.cat_weights[aliases[k]]
        return float(best)

    def score_place(self, place, wiki_entry=None) -> float:
        views = int((wiki_entry or {}).get("views_365", 0))
        return views * self._cat_weight(getattr(place, "kinds", []) or [])

    """ def attach_scores(self, pois, wiki_views):
        for p in pois:
            wv = wiki_views.get(p.xid, {})
            wiki_views[p.xid] = {**wv, "score_rank": self.score_place(p, wv)}
        return wiki_views """
import json
from typing import Iterable, Dict, Set
#perhaps send in a user later? 

class Scorer:
    # single source of truth for defaults
    DEFAULT_CAT_WEIGHTS = {             #here we can change the defaults!
        #promoting: 
        "gardens_and_parks": 2,
        "natural": 1.25,
        "view_points": 1.2,
        "historic": 1.2,
        "museums": 1.1,
        "architecture": 1.05,
        "cultural": 1.1,
        
        #neutral (optional)
        "urban_environment": 1,

        #punishing: 
        "theatres_and_entertainments": 0.2,
        "industrial_facilities": 0.3,
        "foods": 0.3,


    }

    # maps Parent → children
    CATEGORY_GROUPS: Dict[str, Set[str]] = {
        "foods": {"restaurants", "bakeries"},
        "theatres_and_entertainments": {"cinemas"},   #punished same way as cinemas now!
        "historic": {"historic_architecture"},
        "industrial_facilities": {"railway_stations"}
        #add more groups!
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

        self.child_to_parent: Dict[str, str] = {}
        for parent, children in self.CATEGORY_GROUPS.items():
            for child in children:
                self.child_to_parent[child] = parent

    def get_concatinated_kinds(self, kinds) -> Set[str]:
        """ Only one of each parent category!
        """
        kindSet: Set[str] = set()
        for k in kinds:
            parent  = self.child_to_parent.get(k)
            if parent and parent in self.cat_weights:
                kind = parent
            else:
                kind = k
            kindSet.add(kind)
        return kindSet

    # --- scoring logic (tour-like: views × category weight) ---
    def _cat_weight(self, kinds):
        multiplier = 1.0
        for k in self.get_concatinated_kinds(kinds):
            w = self.cat_weights.get(k)
            if w is not None:
                multiplier *= float(w)
        return float(multiplier)

    def score_place(self, place, wiki_entry=None) -> float:
        views = int((wiki_entry or {}).get("views_365", 0))
        return views * self._cat_weight(getattr(place, "kinds", []) or [])
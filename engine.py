"""ResQRoute routing engine: risk-aware Dijkstra and A* on a road graph."""
import heapq
import math
from dataclasses import dataclass, field

SAFE, HIGH_RISK, BLOCKED = "safe", "high_risk", "blocked"
STATUSES = [SAFE, HIGH_RISK, BLOCKED]
RISK_PENALTY = {SAFE: 0.0, HIGH_RISK: 1.0, BLOCKED: 0.0}


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres."""
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@dataclass
class Route:
    nodes: list
    roads: list
    distance: float          # metres
    risk_score: float        # 0 (all safe) .. 1 (all high-risk)
    explored: int            # nodes expanded by the algorithm
    minutes: float = 0.0


@dataclass
class Graph:
    nodes: dict = field(default_factory=dict)   # name -> (lat, lon, is_shelter)
    roads: list = field(default_factory=list)   # dicts: id, a, b, distance, status
    adj: dict = field(default_factory=dict)     # name -> [road ids]

    def add_node(self, name, lat, lon, shelter=False):
        self.nodes[name] = (lat, lon, shelter)
        self.adj.setdefault(name, [])

    def add_road(self, a, b, status=SAFE):
        la, lo, _ = self.nodes[a]
        lb, lob, _ = self.nodes[b]
        dist = haversine(la, lo, lb, lob) * 1.3   # 1.3 = typical road winding factor
        rid = len(self.roads)
        self.roads.append({"id": rid, "a": a, "b": b, "distance": dist, "status": status})
        self.adj[a].append(rid)
        self.adj[b].append(rid)
        return rid

    def set_status(self, rid, status):
        self.roads[rid]["status"] = status

    def shelters(self):
        return [n for n, v in self.nodes.items() if v[2]]

    def find_route(self, start, goal, risk_weight=0.0, algo="astar", extra=None):
        """Cheapest route. risk_weight=0 -> shortest; >0 -> safest.
        algo: 'dijkstra' or 'astar'. extra: {road_id: cost multiplier}."""
        extra = extra or {}
        glat, glon, _ = self.nodes[goal]

        def h(n):
            if algo != "astar":
                return 0.0
            lat, lon, _ = self.nodes[n]
            return haversine(lat, lon, glat, glon)   # admissible: roads are >= straight line

        best = {start: 0.0}
        prev = {}
        pq = [(h(start), 0.0, start)]
        done, explored = set(), 0
        while pq:
            _, g, u = heapq.heappop(pq)
            if u in done:
                continue
            done.add(u)
            explored += 1
            if u == goal:
                break
            for rid in self.adj[u]:
                r = self.roads[rid]
                if r["status"] == BLOCKED:
                    continue
                v = r["b"] if r["a"] == u else r["a"]
                w = r["distance"] * (1 + risk_weight * RISK_PENALTY[r["status"]]) * extra.get(rid, 1.0)
                if g + w < best.get(v, math.inf):
                    best[v] = g + w
                    prev[v] = (u, rid)
                    heapq.heappush(pq, (g + w + h(v), g + w, v))
        if goal not in best:
            return None
        nodes, roads, v = [goal], [], goal
        while v != start:
            v, rid = prev[v]
            nodes.append(v)
            roads.append(rid)
        nodes.reverse()
        roads.reverse()
        dist = sum(self.roads[i]["distance"] for i in roads)
        risky = sum(self.roads[i]["distance"] * RISK_PENALTY[self.roads[i]["status"]] for i in roads)
        return Route(nodes, roads, dist, risky / dist if dist else 0.0, explored,
                     dist / 1000 / 30 * 60)   # assumes 30 km/h average evacuation speed

    def nearest_shelter(self, start, risk_weight=0.0, algo="astar"):
        """Best route to whichever shelter is cheapest to reach."""
        best, best_cost = None, math.inf
        for s in self.shelters():
            if s == start:
                continue
            r = self.find_route(start, s, risk_weight, algo)
            if r:
                cost = sum(self.roads[i]["distance"] * (1 + risk_weight * RISK_PENALTY[self.roads[i]["status"]])
                           for i in r.roads)
                if cost < best_cost:
                    best, best_cost = r, cost
        return best

    def alternative_route(self, start, goal, primary, risk_weight=0.0, algo="astar"):
        """Penalise roads of the primary route (x3) and search again."""
        alt = self.find_route(start, goal, risk_weight, algo, {i: 3.0 for i in primary.roads})
        return alt if alt and alt.roads != primary.roads else None

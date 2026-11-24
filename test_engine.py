"""Run with: python test_engine.py"""
from data import build_default_graph
from engine import BLOCKED, HIGH_RISK

g = build_default_graph()

# 1. A* and Dijkstra must return equally cheap routes
for start in ["Karol Bagh", "Saket", "Civil Lines", "Nehru Place"]:
    for goal in g.shelters():
        a, d = g.find_route(start, goal, 3, "astar"), g.find_route(start, goal, 3, "dijkstra")
        assert abs(a.distance - d.distance) < 1e-6, (start, goal)
print("PASS: A* matches Dijkstra on all tested pairs")

# 2. Safest route should never be riskier than shortest
s, f = g.find_route("Kashmere Gate", "Shelter: DU North Campus", 0), g.find_route("Kashmere Gate", "Shelter: DU North Campus", 3)
assert f.risk_score <= s.risk_score
print("PASS: safest risk <= shortest risk")

# 3. Blocked roads are never used
first = g.find_route("Connaught Place", "Shelter: JLN Stadium", 0)
for i in first.roads:
    g.set_status(i, BLOCKED)
new = g.find_route("Connaught Place", "Shelter: JLN Stadium", 0)
assert new is None or all(g.roads[i]["status"] != BLOCKED for i in new.roads)
print("PASS: blocked roads avoided, route recalculated")

# 4. Fully cut-off node returns None
g2 = build_default_graph()
for rid in g2.adj["Rajouri Garden"]:
    g2.set_status(rid, BLOCKED)
assert g2.find_route("Rajouri Garden", "Shelter: JLN Stadium") is None
print("PASS: unreachable shelter handled")

# 5. Alternative route differs from primary
g3 = build_default_graph()
p = g3.find_route("Connaught Place", "Shelter: JLN Stadium", 3)
alt = g3.alternative_route("Connaught Place", "Shelter: JLN Stadium", p, 3)
assert alt is None or alt.roads != p.roads
print("PASS: alternative route")
r = g.nearest_shelter("Karol Bagh", 3)
print("Demo - nearest shelter from Karol Bagh:", " -> ".join(r.nodes), f"({r.distance/1000:.2f} km)")

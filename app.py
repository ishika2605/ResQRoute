"""ResQRoute - emergency evacuation route finder (Streamlit app)."""
import time
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from data import build_default_graph
from engine import SAFE, HIGH_RISK, BLOCKED, STATUSES

st.set_page_config(page_title="ResQRoute", page_icon="🚨", layout="wide")
COLORS = {SAFE: "#2e9e4f", HIGH_RISK: "#f08c00", BLOCKED: "#d6336c"}
LABELS = {SAFE: "Safe", HIGH_RISK: "High risk", BLOCKED: "Blocked"}

if "g" not in st.session_state:
    st.session_state.g = build_default_graph()
g = st.session_state.g

st.title("🚨 ResQRoute")
st.caption("Emergency evacuation route finder that avoids blocked and high-risk roads. "
           "Simulated data - not for real emergency use.")

# ---------- sidebar controls ----------
with st.sidebar:
    st.header("Plan a route")
    places = [n for n in g.nodes if not g.nodes[n][2]]
    start = st.selectbox("Your location", places)
    dest_opt = st.selectbox("Destination", ["Nearest safe shelter"] + g.shelters())
    mode = st.radio("Route type", ["Safest", "Shortest"], horizontal=True)
    algo = st.radio("Algorithm", ["A*", "Dijkstra"], horizontal=True)
    show_alt = st.checkbox("Show alternative route", value=True)

    st.header("Report road conditions")
    labels = [f"{r['id']}: {r['a']} - {r['b']}" for r in g.roads]
    pick = st.selectbox("Road", labels)
    rid = int(pick.split(":")[0])
    new_status = st.radio("Status", STATUSES, index=STATUSES.index(g.roads[rid]["status"]),
                          format_func=lambda s: LABELS[s], horizontal=True)
    if new_status != g.roads[rid]["status"]:
        g.set_status(rid, new_status)
        st.rerun()
    if st.button("Reset all roads"):
        st.session_state.g = build_default_graph()
        st.rerun()

rw = 3.0 if mode == "Safest" else 0.0
al = "astar" if algo == "A*" else "dijkstra"

# ---------- routing ----------
t0 = time.perf_counter()
if dest_opt == "Nearest safe shelter":
    route = g.nearest_shelter(start, rw, al)
else:
    route = g.find_route(start, dest_opt, rw, al)
ms = (time.perf_counter() - t0) * 1000
goal = route.nodes[-1] if route else None
alt = g.alternative_route(start, goal, route, rw, al) if (route and show_alt) else None

# ---------- metrics ----------
c1, c2, c3, c4, c5 = st.columns(5)
if route:
    c1.metric("Destination", goal.replace("Shelter: ", ""))
    c2.metric("Distance", f"{route.distance/1000:.2f} km")
    c3.metric("Est. time", f"{route.minutes:.0f} min")
    c4.metric("Risk score", f"{route.risk_score:.0%}")
    c5.metric(f"{algo} compute", f"{ms:.2f} ms", f"{route.explored} nodes explored", delta_color="off")
else:
    st.error("⚠️ No safe route available - all paths are blocked. Contact emergency services.")

# ---------- map ----------
lats = [v[0] for v in g.nodes.values()]
lons = [v[1] for v in g.nodes.values()]
m = folium.Map(location=[sum(lats) / len(lats), sum(lons) / len(lons)], zoom_start=12, tiles="CartoDB positron")
for r in g.roads:
    pa, pb = g.nodes[r["a"]][:2], g.nodes[r["b"]][:2]
    folium.PolyLine([pa, pb], color=COLORS[r["status"]], weight=3, opacity=0.7,
                    dash_array="6" if r["status"] != SAFE else None,
                    tooltip=f"{r['a']} - {r['b']} | {LABELS[r['status']]} | {r['distance']:.0f} m").add_to(m)
if alt:
    folium.PolyLine([g.nodes[n][:2] for n in alt.nodes], color="#7048e8", weight=6, opacity=0.8,
                    dash_array="10", tooltip=f"Alternative: {alt.distance/1000:.2f} km").add_to(m)
if route:
    folium.PolyLine([g.nodes[n][:2] for n in route.nodes], color="#1c7ed6", weight=8, opacity=0.95,
                    tooltip=f"Best route: {route.distance/1000:.2f} km").add_to(m)
for n, (la, lo, sh) in g.nodes.items():
    folium.Marker([la, lo], tooltip=n,
                  icon=folium.Icon(color="green" if sh else ("red" if n == start else "gray"),
                                   icon="home" if sh else "info-sign")).add_to(m)
st_folium(m, height=520, use_container_width=True, returned_objects=[])
st.caption("🟢 safe  🟠 high risk (dashed)  🔴 blocked (dashed)  🔵 best route  🟣 alternative route")

# ---------- details + dashboard ----------
left, right = st.columns(2)
with left:
    st.subheader("Route steps")
    if route:
        st.write(" → ".join(route.nodes))
        if alt:
            st.write(f"**Alternative:** {' → '.join(alt.nodes)} ({alt.distance/1000:.2f} km)")
with right:
    st.subheader("Dashboard")
    counts = pd.Series([r["status"] for r in g.roads]).value_counts().reindex(STATUSES, fill_value=0)
    counts.index = [LABELS[s] for s in counts.index]
    st.bar_chart(counts)
    st.caption(f"{len(g.roads)} roads | {len(g.shelters())} shelters | {len(g.nodes)} locations")

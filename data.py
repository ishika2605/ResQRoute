"""Simulated Delhi road network (coordinates are real places; roads/hazards are simulated)."""
from engine import Graph, HIGH_RISK

NODES = [
    ("Connaught Place", 28.6315, 77.2167, False),
    ("India Gate", 28.6129, 77.2295, False),
    ("Karol Bagh", 28.6519, 77.1909, False),
    ("Old Delhi Station", 28.6577, 77.2273, False),
    ("Kashmere Gate", 28.6675, 77.2282, False),
    ("Civil Lines", 28.6812, 77.2228, False),
    ("Rajouri Garden", 28.6492, 77.1219, False),
    ("AIIMS", 28.5672, 77.2100, False),
    ("Lajpat Nagar", 28.5677, 77.2433, False),
    ("Hauz Khas", 28.5494, 77.2001, False),
    ("Saket", 28.5245, 77.2066, False),
    ("Nehru Place", 28.5491, 77.2514, False),
    ("Shelter: JLN Stadium", 28.5827, 77.2340, True),
    ("Shelter: DU North Campus", 28.6889, 77.2100, True),
    ("Shelter: Talkatora Stadium", 28.6370, 77.2000, True),
    ("Shelter: Safdarjung Camp", 28.5685, 77.2070, True),
]

ROADS = [
    ("Connaught Place", "India Gate", None), ("Connaught Place", "Karol Bagh", None),
    ("Connaught Place", "Old Delhi Station", None), ("Connaught Place", "Shelter: Talkatora Stadium", None),
    ("Karol Bagh", "Rajouri Garden", None), ("Karol Bagh", "Shelter: Talkatora Stadium", None),
    ("Karol Bagh", "Kashmere Gate", None), ("Old Delhi Station", "Kashmere Gate", None),
    ("Kashmere Gate", "Civil Lines", HIGH_RISK), ("Civil Lines", "Shelter: DU North Campus", None),
    ("Kashmere Gate", "Shelter: DU North Campus", None),
    ("India Gate", "Shelter: JLN Stadium", None), ("India Gate", "Lajpat Nagar", None),
    ("India Gate", "Shelter: Talkatora Stadium", None), ("India Gate", "Shelter: Safdarjung Camp", HIGH_RISK),
    ("Shelter: Safdarjung Camp", "AIIMS", None), ("AIIMS", "Hauz Khas", None),
    ("AIIMS", "Lajpat Nagar", None), ("Shelter: Safdarjung Camp", "Hauz Khas", None),
    ("Shelter: JLN Stadium", "Lajpat Nagar", None), ("Lajpat Nagar", "Nehru Place", None),
    ("Hauz Khas", "Saket", None), ("Saket", "Nehru Place", None),
]


def build_default_graph():
    g = Graph()
    for n in NODES:
        g.add_node(*n[:3], shelter=n[3])
    for a, b, status in ROADS:
        g.add_road(a, b, status) if status else g.add_road(a, b)
    return g

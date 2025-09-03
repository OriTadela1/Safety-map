import osmnx as ox
import folium
import webbrowser
from pathlib import Path
import argparse

from ratings_utils import load_ratings  # ✅ import from utils


def load_city(city_name="Tel Aviv, Israel"):
    """
    Download city road network from OpenStreetMap.
    Returns a NetworkX graph object.
    """
    G = ox.graph_from_place(city_name, network_type="drive")

    # Initialize safety scores
    for node in G.nodes:
        G.nodes[node]["safety"] = 0.5
    return G


def update_node_safety(G, node, rating):
    """
    Update one node's safety score.
    """
    if node in G.nodes:
        G.nodes[node]["safety"] = rating


def apply_ratings(G, ratings):
    """
    Apply aggregated ratings from ratings.json to the graph.
    ratings is a dict {node_id: [ {user, score, timestamp}, ... ]}
    """
    from statistics import mean

    for node_id, records in ratings.items():
        try:
            node_int = int(node_id)
            if not records:
                continue
            scores = [r["score"] for r in records if "score" in r]
            if not scores:
                continue
            avg_rating = mean(scores)
            update_node_safety(G, node_int, avg_rating)
        except Exception as e:
            print(f"⚠️ Skipped node {node_id}: {e}")


def show_interactive_map(G, filename="map.html"):
    """
    Save the graph as an interactive HTML map and open it in the browser.
    Roads are blue. Nodes are colored by safety (red=unsafe, green=safe).
    Rated nodes appear larger and have popups with details.
    """

    # Convert graph to GeoDataFrames
    nodes, edges = ox.graph_to_gdfs(G)
    center = (nodes["y"].mean(), nodes["x"].mean())
    m = folium.Map(location=center, zoom_start=13)

    # Draw roads (blue polylines)
    for _, row in edges.iterrows():
        coords = [(lat, lon) for lon, lat in row["geometry"].coords]
        folium.PolyLine(coords, color="blue", weight=2, opacity=0.7).add_to(m)

    # Draw nodes with safety colors
    for _, row in nodes.iterrows():
        node_id = row.name
        safety = G.nodes[node_id].get("safety", 0.5)

        # Safety → red (0.0) to green (1.0)
        r = int((1 - safety) * 255)
        g = int(safety * 255)
        color = f"rgb({r},{g},0)"

        # Rated nodes (not default) are bigger and clickable
        if safety != 0.5:
            radius = 8
            popup = folium.Popup(f"Node {node_id} | Safety {safety:.2f}", max_width=200)
        else:
            radius = 4
            popup = None

        folium.CircleMarker(
            location=(row["y"], row["x"]),
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.8,
            popup=popup
        ).add_to(m)

    # Ensure output folder exists
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Save HTML file
    filepath = output_dir / filename
    filepath = filepath.resolve()
    m.save(filepath)

    # Open in default browser
    file_url = filepath.as_uri()
    webbrowser.open_new_tab(file_url)

    print(f"✅ Map saved and opened: {file_url}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load and visualize a city map with safety ratings")
    parser.add_argument("city", nargs="?", default="Tel Aviv, Israel", help="City name (default: Tel Aviv, Israel)")
    args = parser.parse_args()

    G = load_city(args.city)

    ratings = load_ratings()
    apply_ratings(G, ratings)

    safe_filename = args.city.replace(',', '').replace(' ', '_').lower() + ".html"
    show_interactive_map(G, filename=safe_filename)

import osmnx as ox
import folium
import matplotlib
import webbrowser
from pathlib import Path
import argparse
import json
from statistics import mean
from datetime import datetime

def load_city(city_name="Tel Aviv, Israel"):
    """
    Download city road network from OpenStreetMap
    Returns a NetworkX graph object.
    """
    G = ox.graph_from_place(city_name, network_type="drive")
    # Initialize safety scores for all nodes
    for node in G.nodes:
        G.nodes[node]["safety"] = 0.5
    return G

def update_node_safety(G, node, rating):
    """
    Update the safety score of a node.
    rating should be between 0.0 (dangerous) and 1.0 (very safe).

    ##function can not be called manually, it will create conflict
    """
    if node in G.nodes:
        G.nodes[node]["safety"] = rating


def show_interactive_map(G, filename="map.html"):
    """
    Save the graph as an interactive HTML map and open it in the browser.
    The HTML will be placed inside the 'output/' folder.
    """
    # Convert graph to GeoDataFrames
    nodes, edges = ox.graph_to_gdfs(G)

    # Center of the map
    center = (nodes["y"].mean(), nodes["x"].mean())
    m = folium.Map(location=center, zoom_start=13)

    # Draw roads
    for _, row in edges.iterrows():
        coords = [(lat, lon) for lon, lat in row["geometry"].coords]
        folium.PolyLine(coords, color="blue", weight=2, opacity=0.7).add_to(m)

    # Draw nodes with safety colors
    for _, row in nodes.iterrows():
        safety = G.nodes[row.name].get("safety", 0.5)  # default = neutral
        # Convert safety [0,1] into red→green
        r = int((1 - safety) * 255)
        g = int(safety * 255)
        b = 0
        folium.CircleMarker(
            location=(row["y"], row["x"]),
            radius=4,
            color=f"rgb({r},{g},{b})",
            fill=True,
            fill_opacity=0.8
        ).add_to(m)


    # Ensure output folder exists
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Save HTML inside output/
    filepath = output_dir / filename
    filepath = filepath.resolve()
    m.save(filepath)

    # Convert path to file URL
    file_url = filepath.as_uri()
    print(file_url)
    # Open in browser (new tab, more reliable on Windows)
    webbrowser.open_new_tab(file_url)

    print(f"Map saved and opened: {filepath}")

def load_ratings(filename="ratings.json"):
    """
    Load ratings from a JSON file.
    Cleans duplicates: only the latest rating per user is kept.
    Returns a dict {node_id: [ {user, score, timestamp}, ... ]}
    """
    filepath = Path(filename)
    if not filepath.exists():
        print("⚠️ No ratings.json found, using defaults.")
        return {}

    with open(filepath, "r") as f:
        data = json.load(f)

    nodes = data.get("nodes", {})

    cleaned_nodes = {}
    for node_id, records in nodes.items():
        user_latest = {}
        for r in records:
            user = r.get("user", "anonymous")
            score = r.get("score", None)
            ts = r.get("timestamp", None)
            if score is None or ts is None:
                continue

            try:
                ts = datetime.fromisoformat(ts)
            except ValueError:
                print(f"Invalid timestamp for node {node_id}, user {user}: {ts_str}")
                continue

            # Keep the latest timestamp per user
            prev = user_latest.get(user)
            if prev is None or ts > prev["timestamp"]:
                user_latest[user] = {"user": user, "score": score, "timestamp": ts}

        cleaned_nodes[node_id] = list(user_latest.values())
    
    with open(filepath, "w") as f:
        json.dump({"nodes": cleaned_nodes}, f, indent=2)
    
    return cleaned_nodes

def apply_ratings(G, ratings, decay_days=30):
    """
    Apply ratings with time decay.
    Newer ratings count more than older ones.
    """
    now = datetime.utcnow()

    for node_id, records in ratings.items():
        try:
            node_int = int(node_id)
            if not records:
                continue

            weighted_scores = []
            weights = []

            for r in records:
                score = r["score"]
                ts = datetime.fromisoformat(r["timestamp"])

                # Compute decay weight: newer = closer to 1, older = closer to 0
                age_days = (now - ts).days
                weight = max(0.0, 1.0 - age_days / decay_days)

                weighted_scores.append(score * weight)
                weights.append(weight)

            if weights:
                final_score = sum(weighted_scores) / sum(weights)
                update_node_safety(G, node_int, final_score)

        except Exception as e:
            print(f"⚠️ Skipped node {node_id}: {e}")

def save_rating(node_id, score, user="anonymous", filename="ratings.json"):
    """
    Add a new rating record (with user + timestamp) to a node.
    """
    filepath = Path(filename)
    if filepath.exists():
        with open(filepath, "r") as f:
            data = json.load(f)
    else:
        data = {"nodes": {}}

    node_key = str(node_id)
    if node_key not in data["nodes"]:
        data["nodes"][node_key] = []

    # Create a new rating record
    record = {
        "user": user,
        "score": score,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Append rating
    data["nodes"][node_key].append(record)

    # Save back to file
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return data["nodes"]





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load and visualize a city map.")
    parser.add_argument("city", nargs="?", default="Tel Aviv, Israel", help="City name (default: Tel Aviv, Israel)")
    args = parser.parse_args()

    G = load_city(args.city)
    ratings = load_ratings()
    apply_ratings(G, ratings)

    safe_filename = args.city.replace(',', '').replace(' ', '_').lower() + ".html"
    show_interactive_map(G, filename=safe_filename)


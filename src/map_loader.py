import osmnx as ox
import folium
import matplotlib
import webbrowser
from pathlib import Path
import argparse

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load and visualize a city map.")
    parser.add_argument("city", nargs="?", default="Tel Aviv, Israel", help="City name (default: Tel Aviv, Israel)")
    args = parser.parse_args()

    G = load_city(args.city)
    safe_filename = args.city.replace(',', '').replace(' ', '_').lower() + ".html"
    show_interactive_map(G, filename=safe_filename)


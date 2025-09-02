import osmnx as ox
import folium
import matplotlib
import webbrowser
from pathlib import Path

def load_city(city_name="Tel Aviv, Israel"):
    """
    Download city road network from OpenStreetMap.
    Returns a NetworkX graph object.
    """
    G = ox.graph_from_place(city_name, network_type="drive")
    return G

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
    city = "Tel Aviv, Israel"
    G = load_city(city)
    show_interactive_map(G, filename="tel_aviv.html")

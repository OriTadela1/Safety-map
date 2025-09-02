import osmnx as ox

def load_city(city_name="Tel Aviv, Israel"):
    """
    Download city road network from OpenStreetMap.
    Returns a NetworkX graph object.
    """
    G = ox.graph_from_place(city_name, network_type="drive")
    return G

if __name__ == "__main__":
    city = "Tel Aviv, Israel"
    G = load_city(city)
    print(G)
    ox.plot_graph(G)

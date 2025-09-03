import argparse
import random
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ensure we can import from src/
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from map_loader import load_city, show_interactive_map, apply_ratings
from ratings_utils import save_rating, load_ratings


def generate_test_ratings(city, num_users, num_nodes):
    """
    Generate synthetic ratings for a chosen city.
    Each of Y users rates Z nodes with random scores [0,1].
    """
    print(f"Loading city: {city}")
    G = load_city(city)

    all_nodes = list(G.nodes)
    chosen_nodes = random.sample(all_nodes, min(num_nodes, len(all_nodes)))

    users = [f"user_{i+1}" for i in range(num_users)]

    print(f"👥 Users: {len(users)} | 🕸️ Nodes rated: {len(chosen_nodes)}")

    # Generate ratings
    for user in users:
        for node in chosen_nodes:
            score = round(random.uniform(0.0, 1.0), 2)

            # Spread timestamps across last 60 days for realism
            days_ago = random.randint(0, 60)
            ts = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()

            save_rating(node, score, user=user, timestamp=ts)

    # Apply ratings and show map
    ratings = load_ratings()
    apply_ratings(G, ratings)

    safe_filename = f"{city.replace(',', '').replace(' ', '_').lower()}_test.html"
    show_interactive_map(G, filename=safe_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test ratings for a city map")
    parser.add_argument("city", help="City name, e.g. 'Tel Aviv, Israel'")
    parser.add_argument("-y", "--users", type=int, default=5, help="Number of users")
    parser.add_argument("-z", "--nodes", type=int, default=10, help="Number of nodes per user")
    args = parser.parse_args()

    generate_test_ratings(args.city, args.users, args.nodes)

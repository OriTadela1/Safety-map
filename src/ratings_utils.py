import json
from pathlib import Path
from datetime import datetime

def save_rating(node_id, score, user="anonymous", timestamp=None, filename="ratings.json"):
    """
    Add a new rating record to a node.
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

    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    record = {"user": user, "score": score, "timestamp": timestamp}
    data["nodes"][node_key].append(record)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return data["nodes"]

def load_ratings(filename="ratings.json"):
    """
    Load ratings and clean duplicates (latest per user).
    """
    filepath = Path(filename)
    if not filepath.exists():
        print("⚠️ No ratings.json found, using defaults.")
        return {}

    with open(filepath, "r") as f:
        data = json.load(f)

    return data.get("nodes", {})

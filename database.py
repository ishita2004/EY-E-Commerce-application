import json
import os
from datetime import datetime, timezone
from pathlib import Path


STORE_PATH = Path(
    os.environ.get("STORE_DATA_PATH", str(Path(__file__).with_name("store_data.json")))
)
DEFAULT_PRODUCTS = [
    {"id": 101, "name": "Laptop", "price": 1000.0, "weight": 25.0, "stock": 5},
    {"id": 102, "name": "Printer", "price": 3000.0, "weight": 15.0, "stock": 2},
    {"id": 103, "name": "Smartphone", "price": 799.0, "weight": 0.2, "stock": 12},
    {"id": 104, "name": "Headphones", "price": 149.0, "weight": 0.5, "stock": 18},
    {"id": 105, "name": "Keyboard", "price": 89.0, "weight": 0.8, "stock": 25},
    {"id": 106, "name": "Monitor", "price": 349.0, "weight": 6.5, "stock": 10},
    {"id": 107, "name": "Webcam", "price": 79.0, "weight": 0.3, "stock": 20},
    {"id": 108, "name": "Wi-Fi Router", "price": 129.0, "weight": 1.0, "stock": 16},
    {"id": 109, "name": "Tablet", "price": 499.0, "weight": 0.6, "stock": 14},
    {"id": 110, "name": "Desk Lamp", "price": 45.0, "weight": 0.9, "stock": 30},
]


def _empty_store():
    return {
        "users": [],
        "products": [],
        "orders": [],
        "order_items": [],
        "shipments": [],
    }


def save_store(store):
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = STORE_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(store, indent=2), encoding="utf-8")
    temporary_path.replace(STORE_PATH)


def read_store():
    if not STORE_PATH.exists():
        initialize_database()
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def next_id(store, collection):
    return max((int(item["id"]) for item in store[collection]), default=0) + 1


def current_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize_database():
    if STORE_PATH.exists():
        store = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    else:
        store = _empty_store()

    for collection in ("users", "products", "orders", "order_items", "shipments"):
        store.setdefault(collection, [])
    for user in store["users"]:
        user.setdefault("role", "customer")

    existing_product_ids = {product["id"] for product in store["products"]}
    store["products"].extend(
        product.copy()
        for product in DEFAULT_PRODUCTS
        if product["id"] not in existing_product_ids
    )
    save_store(store)
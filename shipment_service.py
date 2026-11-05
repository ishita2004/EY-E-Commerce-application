from database import current_timestamp, next_id, read_store


SHIPPING_RATE_PER_KG = 5.0


def calculate_shipping(weight):
    return weight * SHIPPING_RATE_PER_KG


def create_shipment(store, order_id, shipping_details, weight, cost):
    store["shipments"].append(
        {
            "id": next_id(store, "shipments"),
            "order_id": order_id,
            **shipping_details,
            "weight": weight,
            "cost": cost,
            "status": "Preparing",
            "created_at": current_timestamp(),
        }
    )


def list_shipments(user_id):
    store = read_store()
    orders = {order["id"]: order for order in store["orders"]}
    shipments = []
    for shipment in store["shipments"]:
        order = orders.get(shipment["order_id"])
        if order and order["user_id"] == user_id:
            shipments.append({**shipment, "total": order["total"], "created_at": order["created_at"]})
    return sorted(shipments, key=lambda shipment: shipment["order_id"], reverse=True)
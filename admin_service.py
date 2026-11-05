from database import read_store


LOW_STOCK_THRESHOLD = 5


def get_admin_analytics(user_id):
    store = read_store()
    user = next((user for user in store["users"] if user["id"] == user_id), None)
    if user is None or user["role"] != "admin":
        raise PermissionError("Admin access is required to view store analytics.")

    orders = store["orders"]
    order_items = store["order_items"]
    product_totals = {}
    for item in order_items:
        totals = product_totals.setdefault(
            item["product_id"], {"units_sold": 0, "revenue": 0.0}
        )
        totals["units_sold"] += item["quantity"]
        totals["revenue"] += item["quantity"] * item["unit_price"]

    products = []
    for product in store["products"]:
        totals = product_totals.get(product["id"], {"units_sold": 0, "revenue": 0.0})
        products.append({**product, **totals})
    products.sort(
        key=lambda product: (-product["units_sold"], -product["revenue"], product["name"])
    )

    orders_by_id = {order["id"]: order for order in orders}
    city_totals = {}
    for shipment in store["shipments"]:
        order = orders_by_id.get(shipment["order_id"])
        if order is None:
            continue
        city_key = shipment["city"].strip().casefold()
        city = city_totals.setdefault(
            city_key,
            {"city": shipment["city"], "order_count": 0, "revenue": 0.0, "shipped_weight": 0.0},
        )
        city["order_count"] += 1
        city["revenue"] += order["subtotal"]
        city["shipped_weight"] += shipment["weight"]
    cities = sorted(
        city_totals.values(),
        key=lambda city: (-city["order_count"], -city["revenue"], city["city"]),
    )
    low_stock = [
        {"id": product["id"], "name": product["name"], "stock": product["stock"]}
        for product in store["products"]
        if product["stock"] <= LOW_STOCK_THRESHOLD
    ]
    return {
        "order_count": len(orders),
        "revenue": sum(order["subtotal"] for order in orders),
        "shipping_revenue": sum(order["shipping_cost"] for order in orders),
        "units_sold": sum(item["quantity"] for item in order_items),
        "product_count": len(store["products"]),
        "units_in_stock": sum(product["stock"] for product in store["products"]),
        "products": products,
        "cities": cities,
        "low_stock": low_stock,
    }
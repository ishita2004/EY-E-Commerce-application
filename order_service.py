from database import current_timestamp, next_id, read_store, save_store
from shipment_service import calculate_shipping, create_shipment


def place_order(user_id, cart, shipping_details):
    if not cart:
        raise ValueError("Your cart is empty.")

    store = read_store()
    products = {product["id"]: product for product in store["products"]}
    for product_id, quantity in cart.items():
        product = products.get(product_id)
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")
        if product is None or product["stock"] < quantity:
            raise ValueError(f"Not enough stock for product {product_id}.")

    subtotal = sum(
        products[product_id]["price"] * quantity
        for product_id, quantity in cart.items()
    )
    total_weight = sum(
        products[product_id]["weight"] * quantity
        for product_id, quantity in cart.items()
    )
    shipping_cost = calculate_shipping(total_weight)
    order_id = next_id(store, "orders")
    store["orders"].append(
        {
            "id": order_id,
            "user_id": user_id,
            "subtotal": subtotal,
            "shipping_cost": shipping_cost,
            "total": subtotal + shipping_cost,
            "created_at": current_timestamp(),
        }
    )

    for product_id, quantity in cart.items():
        product = products[product_id]
        store["order_items"].append(
            {
                "id": next_id(store, "order_items"),
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": product["price"],
                "unit_weight": product["weight"],
            }
        )
        product["stock"] -= quantity

    create_shipment(store, order_id, shipping_details, total_weight, shipping_cost)
    save_store(store)
    return order_id, subtotal, total_weight, shipping_cost
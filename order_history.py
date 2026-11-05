from database import read_store


def get_order_history(user_id):
    store = read_store()
    products = {product["id"]: product["name"] for product in store["products"]}
    order_items = {}
    for item in store["order_items"]:
        order_items.setdefault(item["order_id"], []).append(item)

    orders = sorted(
        (order for order in store["orders"] if order["user_id"] == user_id),
        key=lambda order: order["id"],
        reverse=True,
    )
    return [
        {
            **order,
            "items": [
                {
                    **item,
                    "name": products.get(item["product_id"], f"Product {item['product_id']}"),
                }
                for item in order_items.get(order["id"], [])
            ],
        }
        for order in orders
    ]


def main():
    try:
        user_id = int(input("Customer user ID: "))
    except ValueError:
        print("Enter a whole-number user ID.")
        return

    orders = get_order_history(user_id)
    if not orders:
        print("No orders found for that customer.")
        return

    print("\n--- Order history ---")
    for order in orders:
        print(
            f"\nOrder #{order['id']} | {order['created_at']} | "
            f"Total: ${order['total']:.2f}"
        )
        for item in order["items"]:
            line_total = item["quantity"] * item["unit_price"]
            print(
                f"  {item['name']} x {item['quantity']} "
                f"@ ${item['unit_price']:.2f} = ${line_total:.2f}"
            )


if __name__ == "__main__":
    main()

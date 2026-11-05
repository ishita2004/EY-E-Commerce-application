from product_service import list_products


def get_inventory_value():
    products = list_products()
    product_values = [
        {**product, "inventory_value": product["price"] * product["stock"]}
        for product in products
    ]
    return {
        "products": product_values,
        "total_value": sum(product["inventory_value"] for product in product_values),
        "total_units": sum(product["stock"] for product in product_values),
    }


def main():
    inventory = get_inventory_value()
    print("\n--- Inventory value ---")
    for product in inventory["products"]:
        print(
            f"{product['id']} | {product['name']} | "
            f"{product['stock']} in stock | "
            f"${product['inventory_value']:.2f} value"
        )
    print(
        f"\n{inventory['total_units']} units | "
        f"${inventory['total_value']:.2f} total inventory value"
    )


if __name__ == "__main__":
    main()

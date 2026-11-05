from product_service import list_products


def products_under_price(max_price):
    if max_price < 0:
        raise ValueError("Maximum price cannot be negative.")

    return sorted(
        (product for product in list_products() if product["price"] <= max_price),
        key=lambda product: product["price"],
    )


def main():
    try:
        max_price = float(input("Maximum price: "))
        products = products_under_price(max_price)
    except ValueError as error:
        print(f"Enter a valid non-negative price. {error}")
        return

    if not products:
        print("No products found at or below that price.")
        return

    print(f"\n--- Products up to ${max_price:.2f} ---")
    for product in products:
        print(f"{product['id']} | {product['name']} | ${product['price']:.2f}")


if __name__ == "__main__":
    main()

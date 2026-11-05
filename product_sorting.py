from product_service import list_products


def products_by_price():
    return sorted(list_products(), key=lambda product: product["price"])


def main():
    print("\n--- Products by price (low to high) ---")
    for product in products_by_price():
        print(
            f"{product['id']} | {product['name']} | "
            f"${product['price']:.2f} | Stock: {product['stock']}"
        )


if __name__ == "__main__":
    main()

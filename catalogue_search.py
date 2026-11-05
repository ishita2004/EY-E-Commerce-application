from product_service import list_products


def search_products(query):
    search_term = query.strip().casefold()
    if not search_term:
        return []

    return [
        product
        for product in list_products()
        if search_term in product["name"].casefold()
    ]


def main():
    query = input("Search products by name: ")
    matches = search_products(query)

    if not matches:
        print("No matching products found.")
        return

    print("\n--- Matching products ---")
    for product in matches:
        print(
            f"{product['id']} | {product['name']} | "
            f"${product['price']:.2f} | Stock: {product['stock']}"
        )


if __name__ == "__main__":
    main()

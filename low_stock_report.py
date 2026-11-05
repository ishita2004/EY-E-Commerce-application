from product_service import list_products


LOW_STOCK_THRESHOLD = 5


def products_low_in_stock(threshold=LOW_STOCK_THRESHOLD):
    if threshold < 0:
        raise ValueError("Stock threshold cannot be negative.")

    return [
        product
        for product in list_products()
        if product["stock"] <= threshold
    ]


def main():
    products = products_low_in_stock()
    print(f"\n--- Low-stock report ({LOW_STOCK_THRESHOLD} or fewer items) ---")
    if not products:
        print("No products are low on stock.")
        return

    for product in products:
        print(f"{product['id']} | {product['name']} | Stock: {product['stock']}")


if __name__ == "__main__":
    main()

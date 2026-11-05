from database import read_store


def list_products():
    return sorted(read_store()["products"], key=lambda product: product["id"])


def get_product(product_id):
    return next(
        (product for product in read_store()["products"] if product["id"] == product_id),
        None,
    )
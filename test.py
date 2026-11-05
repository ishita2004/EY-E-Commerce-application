import getpass

from admin_service import get_admin_analytics
from database import initialize_database
from order_service import place_order
from product_service import get_product, list_products
from shipment_service import SHIPPING_RATE_PER_KG, list_shipments
from user_service import (
      create_account,
      create_initial_admin,
      has_admin,
      sign_in,
)
from visualization_service import create_admin_visualization


def show_catalogue():
      print("\n--- Store catalogue ---")
      for product in list_products():
            print(
                  f"{product['id']} | {product['name']} | ${product['price']:.2f} | "
                  f"{product['weight']:.1f} kg | Stock: {product['stock']}"
            )


def show_cart(cart):
      if not cart:
            print("Your cart is empty.")
            return

      products = {product["id"]: product for product in list_products()}
      subtotal = 0.0
      weight = 0.0
      print("\n--- Your cart ---")
      for product_id, quantity in cart.items():
            product = products[product_id]
            line_total = product["price"] * quantity
            subtotal += line_total
            weight += product["weight"] * quantity
            print(f"{product['name']} x {quantity}: ${line_total:.2f}")
      print(f"Subtotal: ${subtotal:.2f} | Shipping estimate: ${weight * SHIPPING_RATE_PER_KG:.2f}")


def checkout(user_id, cart):
      if not cart:
            print("Your cart is empty.")
            return

      print("\n--- Shipping address ---")
      shipping_details = {
            "recipient": input("Recipient name: ").strip(),
            "address": input("Street address: ").strip(),
            "city": input("City: ").strip(),
            "postal_code": input("Postal code: ").strip(),
      }
      if not all(shipping_details.values()):
            print("Please fill in every shipping field. Your cart is unchanged.")
            return

      try:
            order_id, subtotal, weight, shipping_cost = place_order(
                  user_id, cart, shipping_details
            )
      except (ValueError, OSError) as error:
            print(f"Checkout could not be completed: {error}")
            return

      cart.clear()
      print(f"Order #{order_id} placed. Subtotal: ${subtotal:.2f}")
      print(f"Shipment: {weight:.1f} kg | Shipping: ${shipping_cost:.2f}")


def show_shipment_dashboard(user_id):
      shipments = list_shipments(user_id)
      print("\n--- Shipment dashboard ---")
      if not shipments:
            print("No shipments yet. Place an order to see your shipping activity.")
            return

      total_weight = sum(shipment["weight"] for shipment in shipments)
      total_shipping = sum(shipment["cost"] for shipment in shipments)
      print(
            f"{len(shipments)} orders | {total_weight:.1f} kg shipped | "
            f"${total_shipping:.2f} total shipping"
      )
      print("\nShipping cost by order")
      max_cost = max(shipment["cost"] for shipment in shipments)
      for shipment in reversed(shipments):
            bar_length = round(shipment["cost"] / max_cost * 32) if max_cost else 0
            print(
                  f"#{shipment['order_id']:>4} | {'#' * bar_length:<32} "
                  f"${shipment['cost']:.2f} | {shipment['weight']:.1f} kg"
            )
      print("\nRecent deliveries")
      for shipment in shipments[:5]:
            destination = (
                  f"{shipment['recipient']}, {shipment['address']}, "
                  f"{shipment['city']} {shipment['postal_code']}"
            )
            print(
                  f"Order #{shipment['order_id']} | {shipment['status']} | "
                  f"{destination} | {shipment['created_at']}"
            )


def show_admin_dashboard(user):
      try:
            analytics = get_admin_analytics(user.id)
      except PermissionError as error:
            print(error)
            return

      print("\n--- Store admin analytics ---")
      print(
            f"{analytics['order_count']} orders | {analytics['units_sold']} units sold | "
            f"${analytics['revenue']:.2f} sales | "
            f"${analytics['shipping_revenue']:.2f} shipping"
      )
      print(
            f"{analytics['product_count']} products | "
            f"{analytics['units_in_stock']} units in stock"
      )
      image_path = create_admin_visualization(analytics)
      print(f"Analytics chart saved to {image_path}")


def setup_initial_admin():
      print("\n--- First-time admin setup ---")
      print("Create the store's first admin account. Existing accounts remain customers.")
      while not has_admin():
            username = input("Admin username: ").strip()
            password = getpass.getpass("Admin password (at least 8 characters): ")
            confirmation = getpass.getpass("Confirm password: ")
            if password != confirmation:
                  print("Passwords do not match. Try again.")
                  continue
            user = create_initial_admin(username, password)
            if user:
                  print(f"Admin account created for {user.username}.")


def sign_up():
      print("\n--- Create account ---")
      username = input("Username: ")
      password = getpass.getpass("Password (at least 8 characters): ")
      confirmation = getpass.getpass("Confirm password: ")
      if password != confirmation:
            print("Passwords do not match.")
            return None
      user = create_account(username, password)
      if user:
            print(f"Account created. Welcome, {user.username}!")
      return user


def sign_in_prompt():
      print("\n--- Sign in ---")
      username = input("Username: ")
      password = getpass.getpass("Password: ")
      user = sign_in(username, password)
      if user is None:
            print("Username or password is incorrect.")
      else:
            print(f"Welcome back, {user.username}!")
      return user


def shopping_session(user):
      cart = {}
      is_admin = user.role == "admin"
      sign_out_option = "7" if is_admin else "6"
      exit_option = "8" if is_admin else "7"
      while True:
            print(f"\n--- Mini Store | signed in as {user.username} ---")
            print("1. View catalogue")
            print("2. Add item to cart")
            print("3. View cart")
            print("4. Checkout and ship")
            print("5. Shipment dashboard")
            if is_admin:
                  print("6. Admin analytics")
            print(f"{sign_out_option}. Sign out")
            print(f"{exit_option}. Exit")
            choice = input(f"Choose an option (1-{exit_option}): ").strip()

            if choice == "1":
                  show_catalogue()
            elif choice == "2":
                  try:
                        product_id = int(input("Product ID: "))
                        quantity = int(input("Quantity: "))
                        product = get_product(product_id)
                        if product is None or quantity < 1:
                              print("Choose a listed product and a quantity of at least 1.")
                        elif cart.get(product_id, 0) + quantity > product["stock"]:
                              print(f"Only {product['stock']} in stock.")
                        else:
                              cart[product_id] = cart.get(product_id, 0) + quantity
                              print(f"Added {quantity} x {product['name']} to your cart.")
                  except ValueError:
                        print("Enter whole numbers for product ID and quantity.")
            elif choice == "3":
                  show_cart(cart)
            elif choice == "4":
                  checkout(user.id, cart)
            elif choice == "5":
                  show_shipment_dashboard(user.id)
            elif choice == "6" and is_admin:
                  show_admin_dashboard(user)
            elif choice == sign_out_option:
                  print("Signed out.")
                  return
            elif choice == exit_option:
                  return False
            else:
                  print(f"Choose an option from 1 to {exit_option}.")


def main():
      initialize_database()
      if not has_admin():
            setup_initial_admin()
      while True:
            print("\n--- Mini Store ---")
            print("1. Sign up")
            print("2. Sign in")
            print("3. Exit")
            choice = input("Choose an option (1-3): ").strip()
            if choice == "1":
                  user = sign_up()
            elif choice == "2":
                  user = sign_in_prompt()
            elif choice == "3":
                  print("Goodbye.")
                  return
            else:
                  print("Choose an option from 1 to 3.")
                  continue

            if user and shopping_session(user) is False:
                  print("Goodbye.")
                  return


if __name__ == "__main__":
      main()



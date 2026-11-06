import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from admin_service import get_admin_analytics
from database import initialize_database
from order_service import place_order
from product_service import get_product, list_products
from shipment_service import SHIPPING_RATE_PER_KG, list_shipments
from user_service import create_account, create_initial_admin, has_admin, sign_in


WEB_ROOT = Path(__file__).with_name("web")
MAX_REQUEST_BYTES = 64 * 1024
SESSION_COOKIE = "mini_store_session"
SESSION_MAX_AGE = 60 * 60 * 24
_sessions = {}
_sessions_lock = threading.RLock()
_store_lock = threading.RLock()


class StoreRequestHandler(BaseHTTPRequestHandler):
    server_version = "MiniStore/1.0"

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self._send_file("index.html")
            return
        if path in ("/styles.css", "/app.js"):
            self._send_file(path.lstrip("/"))
            return

        if path == "/api/products":
            with _store_lock:
                self._send_json(200, {"products": list_products()})
            return

        session = self._get_session()
        if path == "/api/session":
            with _store_lock:
                user = self._current_user(session)
                self._send_json(
                    200,
                    {
                        "user": user,
                        "cart": self._cart_items(session),
                        "shipping_rate": SHIPPING_RATE_PER_KG,
                        "admin_setup_required": not has_admin(),
                    },
                )
        elif path == "/api/shipments":
            user = self._require_user(session)
            if user is None:
                return
            with _store_lock:
                self._send_json(200, {"shipments": list_shipments(user["id"])})
        elif path == "/api/admin/analytics":
            user = self._require_user(session)
            if user is None:
                return
            try:
                with _store_lock:
                    analytics = get_admin_analytics(user["id"])
            except PermissionError:
                self._send_json(403, {"error": "Admin access is required to view store analytics."})
                return
            self._send_json(200, analytics)
        else:
            self._send_json(404, {"error": "Not found."})

    def do_POST(self):
        path = urlsplit(self.path).path
        if not path.startswith("/api/"):
            self._send_json(404, {"error": "Not found."})
            return

        session = self._get_session()
        payload = self._read_json()
        if payload is None:
            return

        if path in ("/api/signup", "/api/signin"):
            self._authenticate(path, payload, session)
        elif path == "/api/signout":
            with _sessions_lock:
                session["user_id"] = None
                session["cart"] = {}
            self._send_json(200, {"user": None, "cart": []})
        elif path == "/api/cart":
            self._update_cart(payload, session)
        elif path == "/api/checkout":
            self._checkout(payload, session)
        else:
            self._send_json(404, {"error": "Not found."})

    def do_DELETE(self):
        if urlsplit(self.path).path != "/api/cart":
            self._send_json(404, {"error": "Not found."})
            return
        session = self._get_session()
        with _sessions_lock:
            session["cart"] = {}
        self._send_json(200, {"cart": []})

    def _authenticate(self, path, payload, session):
        username = payload.get("username")
        password = payload.get("password")
        if not isinstance(username, str) or not isinstance(password, str):
            self._send_json(400, {"error": "Enter a username and password."})
            return
        username = username.strip()
        if not 3 <= len(username) <= 32 or len(password) < 8:
            self._send_json(
                400,
                {"error": "Use a 3–32 character username and a password of at least 8 characters."},
            )
            return

        try:
            with _store_lock:
                if path == "/api/signup":
                    user = (
                        create_initial_admin(username, password)
                        if not has_admin()
                        else create_account(username, password)
                    )
                else:
                    user = sign_in(username, password)
        except OSError:
            self._send_json(500, {"error": "The account service is temporarily unavailable."})
            return
        if user is None:
            message = (
                "That username is already in use."
                if path == "/api/signup"
                else "Username or password is incorrect."
            )
            self._send_json(409 if path == "/api/signup" else 401, {"error": message})
            return

        token = secrets.token_urlsafe(32)
        with _sessions_lock:
            session["user_id"] = user.id
            _sessions[token] = session
            old_token = self._session_token
            if old_token:
                _sessions.pop(old_token, None)
        self._session_token = token
        self._new_session_token = token
        self._send_json(
            200,
            {
                "user": {"id": user.id, "username": user.username, "role": user.role},
                "cart": self._cart_items(session),
            },
        )

    def _update_cart(self, payload, session):
        product_id = payload.get("product_id")
        quantity = payload.get("quantity")
        if (
            isinstance(product_id, bool)
            or not isinstance(product_id, int)
            or isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity < 0
        ):
            self._send_json(400, {"error": "Choose a valid product and quantity."})
            return

        with _store_lock:
            product = get_product(product_id)
            if product is None:
                self._send_json(404, {"error": "That product is no longer available."})
                return
            if quantity > product["stock"]:
                self._send_json(
                    400,
                    {"error": f"Only {product['stock']} of {product['name']} are in stock."},
                )
                return
            with _sessions_lock:
                if quantity:
                    session["cart"][product_id] = quantity
                else:
                    session["cart"].pop(product_id, None)
            self._send_json(200, {"cart": self._cart_items(session)})

    def _checkout(self, payload, session):
        user = self._require_user(session)
        if user is None:
            return
        shipping_fields = ("recipient", "address", "city", "postal_code")
        shipping_details = {}
        for field in shipping_fields:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
                self._send_json(400, {"error": "Complete each shipping field (200 characters max)."})
                return
            shipping_details[field] = value.strip()

        with _sessions_lock:
            cart = dict(session["cart"])
        try:
            with _store_lock:
                order_id, subtotal, weight, shipping_cost = place_order(
                    user["id"], cart, shipping_details
                )
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
        except OSError:
            self._send_json(500, {"error": "The order could not be saved. Please try again."})
            return

        with _sessions_lock:
            session["cart"] = {}
        self._send_json(
            201,
            {
                "order_id": order_id,
                "subtotal": subtotal,
                "weight": weight,
                "shipping_cost": shipping_cost,
                "total": subtotal + shipping_cost,
                "cart": [],
            },
        )

    def _read_json(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid request size."})
            return None
        if content_length < 0 or content_length > MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request is too large."})
            return None
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": "Send request data as JSON."})
            return None
        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Invalid JSON request."})
            return None
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Invalid request data."})
            return None
        return payload

    def _get_session(self):
        if hasattr(self, "_session"):
            return self._session
        token = None
        for cookie in self.headers.get_all("Cookie", []):
            for item in cookie.split(";"):
                name, separator, value = item.strip().partition("=")
                if separator and name == SESSION_COOKIE:
                    token = value
        with _sessions_lock:
            session = _sessions.get(token) if token else None
            if session is None:
                token = secrets.token_urlsafe(32)
                session = {"user_id": None, "cart": {}}
                _sessions[token] = session
                self._new_session_token = token
        self._session = session
        self._session_token = token
        return session

    def _current_user(self, session):
        user_id = session.get("user_id")
        if user_id is None:
            return None
        from database import read_store

        user = next((item for item in read_store()["users"] if item["id"] == user_id), None)
        if user is None:
            with _sessions_lock:
                session["user_id"] = None
            return None
        return {"id": user["id"], "username": user["username"], "role": user["role"]}

    def _require_user(self, session):
        with _store_lock:
            user = self._current_user(session)
        if user is None:
            self._send_json(401, {"error": "Sign in to continue."})
        return user

    def _cart_items(self, session):
        with _sessions_lock:
            return [
                {"product_id": product_id, "quantity": quantity}
                for product_id, quantity in session["cart"].items()
            ]

    def _send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self._send_headers("application/json; charset=utf-8", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filename):
        path = WEB_ROOT / filename
        try:
            body = path.read_bytes()
        except OSError:
            self._send_json(404, {"error": "Page not found."})
            return
        content_type = "text/html; charset=utf-8" if filename.endswith(".html") else (
            "text/css; charset=utf-8" if filename.endswith(".css") else "text/javascript; charset=utf-8"
        )
        self.send_response(200)
        self._send_headers(content_type, len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_headers(self, content_type, content_length):
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        if getattr(self, "_new_session_token", None):
            secure_cookie = (
                "; Secure"
                if os.environ.get("SECURE_COOKIE", "").casefold() in ("1", "true", "yes")
                else ""
            )
            self.send_header(
                "Set-Cookie",
                f"{SESSION_COOKIE}={self._new_session_token}; Path=/; HttpOnly; "
                f"SameSite=Strict; Max-Age={SESSION_MAX_AGE}{secure_cookie}",
            )

    def log_message(self, format_string, *args):
        super().log_message(format_string, *args)


class StoreHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    initialize_database()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", os.environ.get("WEBSITE_PORT", "8000")))
    server = StoreHTTPServer((host, port), StoreRequestHandler)
    print(f"Mini Store is ready on {host}:{port} (press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMini Store stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

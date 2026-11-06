const state = {
  products: [],
  user: null,
  cart: [],
  shippingRate: 5,
  adminSetupRequired: false,
};

const productGrid = document.querySelector("#product-grid");
const overlay = document.querySelector("#overlay");
const dialog = document.querySelector("#dialog");
const dialogContent = document.querySelector("#dialog-content");
const toast = document.querySelector("#toast");

const productArt = {
  Laptop: ["💻", "work & create"],
  Printer: ["🖨️", "work & create"],
  Smartphone: ["📱", "stay connected"],
  Headphones: ["🎧", "sound good"],
  Keyboard: ["⌨️", "work & create"],
  Monitor: ["🖥️", "work & create"],
  Webcam: ["📷", "stay connected"],
  "Wi-Fi Router": ["📡", "stay connected"],
  Tablet: ["📲", "work & create"],
  "Desk Lamp": ["💡", "make a space"],
};

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  let result;
  try {
    result = await response.json();
  } catch {
    throw new Error("The store returned an unexpected response.");
  }
  if (!response.ok) {
    throw new Error(result.error || "Something went wrong. Please try again.");
  }
  return result;
}

function money(amount) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

function notify(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(notify.timeout);
  notify.timeout = setTimeout(() => toast.classList.remove("visible"), 2600);
}

function updateHeader() {
  const accountButton = document.querySelector("#account-button");
  const ordersLink = document.querySelector("#orders-link");
  accountButton.textContent = state.user ? state.user.username : "Sign in";
  ordersLink.hidden = !state.user;
  ordersLink.textContent = state.user?.role === "admin" ? "Store insights" : "My orders";
  const count = state.cart.reduce((total, item) => total + item.quantity, 0);
  document.querySelector("#cart-count").textContent = count;
}

function renderProducts() {
  const search = document.querySelector("#search-input").value.trim().toLowerCase();
  const sort = document.querySelector("#sort-select").value;
  let products = state.products.filter((product) => product.name.toLowerCase().includes(search));
  if (sort === "price-low") products = [...products].sort((a, b) => a.price - b.price);
  if (sort === "price-high") products = [...products].sort((a, b) => b.price - a.price);
  if (sort === "name") products = [...products].sort((a, b) => a.name.localeCompare(b.name));

  document.querySelector("#product-count").textContent =
    `${products.length} good ${products.length === 1 ? "find" : "finds"} for you`;
  if (!products.length) {
    productGrid.innerHTML = '<div class="empty-state">No finds just yet. Try another search.</div>';
    return;
  }

  productGrid.innerHTML = products.map((product, index) => {
    const [emoji, label] = productArt[product.name] || ["✳", "everyday find"];
    const stockText = product.stock === 0 ? "Out of stock" : `${product.stock} in stock`;
    return `
      <article class="product-card">
        <div class="product-visual tone-${(index % 4) + 1}">
          <span class="product-tag">${escapeHTML(label)}</span>
          <span class="product-emoji" aria-hidden="true">${emoji}</span>
        </div>
        <div class="product-info">
          <div>
            <h3 class="product-name">${escapeHTML(product.name)}</h3>
            <p class="product-detail">${Number(product.weight).toFixed(1)} kg · Item ${product.id}</p>
          </div>
          <p class="product-price">${money(product.price)}</p>
        </div>
        <div class="product-actions">
          <span class="stock-copy">${stockText}</span>
          <button class="add-button" type="button" aria-label="Add ${escapeHTML(product.name)} to bag"
            data-add="${product.id}" ${product.stock === 0 ? "disabled" : ""}>+</button>
        </div>
      </article>`;
  }).join("");
}

function showDialog(content, wide = false) {
  dialogContent.innerHTML = content;
  dialog.classList.toggle("wide", wide);
  overlay.hidden = false;
  document.body.style.overflow = "hidden";
  dialog.querySelector("input, button, select")?.focus();
}

function closeDialog() {
  overlay.hidden = true;
  document.body.style.overflow = "";
}

function showSignIn(mode = state.adminSetupRequired ? "signup" : "signin") {
  if (state.user) {
    showDialog(`
      <p class="eyebrow">YOUR GOOD THINGS ACCOUNT</p>
      <h2 id="dialog-title">Hello, ${escapeHTML(state.user.username)}.</h2>
      <p class="dialog-intro">Signed in as ${escapeHTML(state.user.role)}.</p>
      <button class="primary-button dialog-submit" id="signout-button" type="button">Sign out</button>`);
    return;
  }
  const signingUp = mode === "signup";
  showDialog(`
    <p class="eyebrow">${state.adminSetupRequired ? "FIRST-TIME SETUP" : "A LITTLE MORE PERSONAL"}</p>
    <h2 id="dialog-title">${state.adminSetupRequired ? "Set up your store." : signingUp ? "Join the good list." : "Welcome back."}</h2>
    <p class="dialog-intro">${state.adminSetupRequired ? "Create the first account to become the store admin." : signingUp ? "Create an account to keep your orders close." : "Sign in to pick up where you left off."}</p>
    <form id="auth-form" data-mode="${mode}">
      <label class="form-field">Username
        <input name="username" minlength="3" maxlength="32" autocomplete="username" required>
      </label>
      <label class="form-field">Password
        <input name="password" type="password" minlength="8" autocomplete="${signingUp ? "new-password" : "current-password"}" required>
      </label>
      ${signingUp ? `<label class="form-field">Confirm password
        <input name="confirmation" type="password" minlength="8" autocomplete="new-password" required>
      </label>` : ""}
      <button class="primary-button dialog-submit" type="submit">${state.adminSetupRequired ? "Create admin account" : signingUp ? "Create account" : "Sign in"} <span>↗</span></button>
    </form>
    ${state.adminSetupRequired ? "" : `<p class="auth-switch">${signingUp ? "Already have an account?" : "New around here?"}
      <button class="inline-button" id="auth-switch" type="button">${signingUp ? "Sign in" : "Create one"}</button>
    </p>`}`);
}

function cartTotals() {
  return state.cart.reduce((totals, item) => {
    const product = state.products.find((candidate) => candidate.id === item.product_id);
    if (product) {
      totals.subtotal += product.price * item.quantity;
      totals.weight += product.weight * item.quantity;
    }
    return totals;
  }, { subtotal: 0, weight: 0 });
}

function renderCart() {
  const lines = state.cart.map((item) => {
    const product = state.products.find((candidate) => candidate.id === item.product_id);
    if (!product) return "";
    const [emoji] = productArt[product.name] || ["✳"];
    return `
      <div class="cart-row">
        <span class="cart-thumb" aria-hidden="true">${emoji}</span>
        <div><p class="cart-row-name">${escapeHTML(product.name)}</p>
          <p class="cart-row-price">${money(product.price)} each</p></div>
        <div class="quantity-control">
          <button type="button" aria-label="Remove one ${escapeHTML(product.name)}" data-quantity="${product.id}" data-change="-1">−</button>
          <span>${item.quantity}</span>
          <button type="button" aria-label="Add one ${escapeHTML(product.name)}" data-quantity="${product.id}" data-change="1" ${item.quantity >= product.stock ? "disabled" : ""}>+</button>
        </div>
      </div>`;
  }).join("");
  const { subtotal, weight } = cartTotals();
  const shipping = weight * state.shippingRate;
  const empty = state.cart.length === 0;
  showDialog(`
    <p class="eyebrow">YOUR EVERYDAY EDIT</p>
    <h2 id="dialog-title">${empty ? "Your bag is taking a breather." : "Your bag."}</h2>
    ${empty ? '<p class="dialog-intro">The good stuff is right over there.</p><a class="primary-button" href="#shop" id="continue-shopping">Explore the shop <span>↘</span></a>' : `
      <div class="cart-list">${lines}</div>
      <div class="cart-summary"><span>Subtotal</span><strong>${money(subtotal)}</strong></div>
      <div class="cart-summary"><span>Shipping estimate · ${weight.toFixed(1)} kg</span><strong>${money(shipping)}</strong></div>
      <div class="cart-summary cart-total"><span>Estimated total</span><strong>${money(subtotal + shipping)}</strong></div>
      <p class="cart-footnote">Shipping is $${state.shippingRate.toFixed(2)} per kg. Final total is confirmed at checkout.</p>
      ${state.user ? `
        <form class="checkout-form" id="checkout-form">
          <p class="eyebrow">WHERE SHOULD IT GO?</p>
          <div class="form-grid">
            <label class="form-field">Recipient<input name="recipient" maxlength="200" autocomplete="name" required></label>
            <label class="form-field">Street address<input name="address" maxlength="200" autocomplete="street-address" required></label>
            <label class="form-field">City<input name="city" maxlength="200" autocomplete="address-level2" required></label>
            <label class="form-field">Postal code<input name="postal_code" maxlength="200" autocomplete="postal-code" required></label>
          </div>
          <button class="primary-button dialog-submit" type="submit">Place order · ${money(subtotal + shipping)} <span>↗</span></button>
        </form>` : `
        <button class="primary-button dialog-submit" id="cart-signin" type="button">Sign in to checkout <span>↗</span></button>
        <p class="auth-switch">Your bag will be here when you sign in.</p>`}
      <p class="auth-switch"><button class="inline-button" id="clear-cart" type="button">Empty the bag</button></p>`}
  `, true);
}

async function openOrders() {
  try {
    const result = await request("/api/shipments");
    const orders = result.shipments;
    showDialog(`
      <p class="eyebrow">YOUR GOOD THINGS</p>
      <h2 id="dialog-title">Order trail.</h2>
      ${orders.length ? `<div class="order-list">${orders.map((order) => `
        <article class="order-card">
          <div class="order-card-head"><span>Order #${order.order_id}</span><span class="order-status">${escapeHTML(order.status)}</span></div>
          <p class="order-detail">${escapeHTML(order.recipient)} · ${escapeHTML(order.address)}, ${escapeHTML(order.city)} ${escapeHTML(order.postal_code)}</p>
          <p class="order-detail">${new Date(order.created_at).toLocaleDateString()} · ${Number(order.weight).toFixed(1)} kg · ${money(order.total)}</p>
        </article>`).join("")}</div>` : '<p class="dialog-intro">No orders yet. Your first good find is waiting.</p>'}
    `, true);
  } catch (error) {
    notify(error.message);
  }
}

async function openAnalytics() {
  try {
    const data = await request("/api/admin/analytics");
    const bestsellers = data.products.filter((product) => product.units_sold > 0).slice(0, 6);
    showDialog(`
      <p class="eyebrow">THE BIG PICTURE</p>
      <h2 id="dialog-title">Store insights.</h2>
      <div class="admin-stats">
        <div class="stat-card"><p class="stat-label">Orders</p><p class="stat-value">${data.order_count}</p></div>
        <div class="stat-card"><p class="stat-label">Sales</p><p class="stat-value">${money(data.revenue)}</p></div>
        <div class="stat-card"><p class="stat-label">Units in stock</p><p class="stat-value">${data.units_in_stock}</p></div>
      </div>
      <p class="eyebrow">BESTSELLERS</p>
      ${bestsellers.length ? `<table class="admin-table"><thead><tr><th>Product</th><th>Sold</th><th>Left</th></tr></thead><tbody>
        ${bestsellers.map((product) => `<tr><td>${escapeHTML(product.name)}</td><td>${product.units_sold}</td><td class="${product.stock <= 5 ? "low-stock" : ""}">${product.stock}</td></tr>`).join("")}
      </tbody></table>` : '<p class="dialog-intro">No sales to show yet.</p>'}
    `, true);
  } catch (error) {
    notify(error.message);
  }
}

productGrid.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-add]");
  if (!button) return;
  const product = state.products.find((item) => item.id === Number(button.dataset.add));
  const current = state.cart.find((item) => item.product_id === product.id)?.quantity || 0;
  try {
    const result = await request("/api/cart", {
      method: "POST",
      body: JSON.stringify({ product_id: product.id, quantity: current + 1 }),
    });
    state.cart = result.cart;
    updateHeader();
    notify(`${product.name} added to your bag.`);
  } catch (error) {
    notify(error.message);
  }
});

document.querySelector("#search-input").addEventListener("input", renderProducts);
document.querySelector("#sort-select").addEventListener("change", renderProducts);
document.querySelector("#cart-button").addEventListener("click", renderCart);
document.querySelector("#account-button").addEventListener("click", () => showSignIn());
document.querySelector("#orders-link").addEventListener("click", () => {
  if (state.user?.role === "admin") openAnalytics();
  else openOrders();
});
document.querySelector("#dialog-close").addEventListener("click", closeDialog);
document.querySelector(".overlay-backdrop").addEventListener("click", closeDialog);
overlay.addEventListener("click", (event) => {
  if (event.target.closest("#auth-switch")) {
    showSignIn(event.target.closest("#auth-form")?.dataset.mode === "signup" ? "signin" : "signup");
  }
  if (event.target.closest("#signout-button")) {
    request("/api/signout", { method: "POST", body: "{}" })
      .then((result) => {
        state.user = result.user;
        state.cart = result.cart;
        state.adminSetupRequired = false;
        updateHeader();
        closeDialog();
        notify("You’re signed out. See you soon.");
      })
      .catch((error) => notify(error.message));
  }
  if (event.target.closest("#cart-signin")) showSignIn("signin");
  if (event.target.closest("#continue-shopping")) closeDialog();
  if (event.target.closest("#clear-cart")) {
    request("/api/cart", { method: "DELETE" })
      .then((result) => {
        state.cart = result.cart;
        updateHeader();
        renderCart();
      })
      .catch((error) => notify(error.message));
  }
});

overlay.addEventListener("click", async (event) => {
  const quantityButton = event.target.closest("[data-quantity]");
  if (!quantityButton) return;
  const productId = Number(quantityButton.dataset.quantity);
  const item = state.cart.find((entry) => entry.product_id === productId);
  if (!item) return;
  try {
    const result = await request("/api/cart", {
      method: "POST",
      body: JSON.stringify({
        product_id: productId,
        quantity: item.quantity + Number(quantityButton.dataset.change),
      }),
    });
    state.cart = result.cart;
    updateHeader();
    renderCart();
  } catch (error) {
    notify(error.message);
  }
});

overlay.addEventListener("submit", async (event) => {
  const form = event.target;
  if (form.id !== "auth-form" && form.id !== "checkout-form") return;
  event.preventDefault();
  const formData = new FormData(form);
  if (form.id === "auth-form") {
    const mode = form.dataset.mode;
    const password = formData.get("password");
    if (mode === "signup" && password !== formData.get("confirmation")) {
      notify("Those passwords don’t match.");
      return;
    }
    const submit = form.querySelector('[type="submit"]');
    submit.disabled = true;
    try {
      const result = await request(`/api/${mode}`, {
        method: "POST",
        body: JSON.stringify({
          username: formData.get("username"),
          password,
        }),
      });
      state.user = result.user;
      state.cart = result.cart;
      updateHeader();
      closeDialog();
      notify(`Good to have you, ${state.user.username}.`);
    } catch (error) {
      notify(error.message);
      submit.disabled = false;
    }
    return;
  }

  const submit = form.querySelector('[type="submit"]');
  submit.disabled = true;
  try {
    const result = await request("/api/checkout", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(formData)),
    });
    state.cart = result.cart;
    updateHeader();
    showDialog(`
      <p class="eyebrow">A GOOD THING IS ON ITS WAY</p>
      <h2 id="dialog-title">Order placed.</h2>
      <p class="dialog-intro">Order #${result.order_id} is getting ready for ${escapeHTML(formData.get("recipient"))}.</p>
      <div class="cart-summary"><span>Subtotal</span><strong>${money(result.subtotal)}</strong></div>
      <div class="cart-summary"><span>Shipping · ${Number(result.weight).toFixed(1)} kg</span><strong>${money(result.shipping_cost)}</strong></div>
      <div class="cart-summary cart-total"><span>Total</span><strong>${money(result.total)}</strong></div>
      <button class="primary-button dialog-submit" id="done-button" type="button">Lovely <span>✳</span></button>
    `);
    notify(`Order #${result.order_id} is in!`);
  } catch (error) {
    notify(error.message);
    submit.disabled = false;
  }
});

overlay.addEventListener("click", (event) => {
  if (event.target.closest("#done-button")) closeDialog();
});

async function startStore() {
  try {
    const [session, catalogue] = await Promise.all([
      request("/api/session"),
      request("/api/products"),
    ]);
    state.user = session.user;
    state.cart = session.cart;
    state.shippingRate = session.shipping_rate;
    state.adminSetupRequired = session.admin_setup_required;
    state.products = catalogue.products;
    updateHeader();
    renderProducts();
  } catch (error) {
    productGrid.innerHTML = `<div class="empty-state">${escapeHTML(error.message)} Refresh to try again.</div>`;
  }
}

startStore();

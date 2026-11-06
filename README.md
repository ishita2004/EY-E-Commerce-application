# Mini Store

A small shop where customers can browse products, place orders, and track
shipments from the command line or a browser. Store admins can view sales
analytics and create a chart.

## Run it on Windows

1. Install Python 3.10 or newer.
2. Open PowerShell in this project folder.
3. Install the required chart packages:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Start the store:

   ```powershell
   py test.py
   ```

   You can also double-click `run_store.bat`.

## Open the web storefront

1. Install Python 3.10 or newer.
2. From this folder, run:

   ```powershell
   py web_server.py
   ```

3. Open <http://127.0.0.1:8000> in your browser. Press **Ctrl+C** in the
   terminal to stop the server.

On Windows, you can also double-click `run_store_web.bat`.

The web storefront uses the same accounts, products, orders, and shipments as
the command-line shop. Sign up for a customer account or sign in with an
existing account. Admin accounts can open **Store insights**. The web server
only listens on this computer; keep the terminal open while using the store.

## Deploy to Azure App Service

The Python storefront can run on a Linux App Service. In Azure, create a
**Web App** with **Code** publishing and a supported Python runtime, then set:

- Startup command: `python web_server.py`
- `HOST`: `0.0.0.0` (binds to the App Service network interface)
- `STORE_DATA_PATH`: `/home/data/store_data.json` (keeps store data outside the
  deployed application files)
- `SECURE_COOKIE`: `1` (marks sign-in cookies as HTTPS-only)
- `SCM_DO_BUILD_DURING_DEPLOYMENT`: `true`

In **Deployment Center**, connect the GitHub repository and select the
`feature/inventory-value-report` branch to deploy the storefront. App Service
must run a single instance: sessions and the JSON store are not shared across
multiple instances. The JSON file is suitable for a small demo; use a managed
database and shared session storage for a production, scaled store.

## Deploy to an Azure Ubuntu VM with Apache

Do not use the repository root as Apache's `DocumentRoot`: that exposes source
files and the checked-in sample store data, and it does not run the Python API.
The files in `deploy/` configure Apache to proxy requests to the Python
application instead.

On the VM, install Python, Apache, and Git, then clone the deployment branch
outside Apache's web directories:

```bash
sudo apt update
sudo apt install -y apache2 git python3 python3-venv
sudo mkdir -p /opt/mini-store /var/lib/mini-store
sudo chown "$USER":"$USER" /opt/mini-store
git clone --branch feature/inventory-value-report https://github.com/ishita2004/EY-E-Commerce-application.git /opt/mini-store
cd /opt/mini-store
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo chown -R root:root /opt/mini-store
sudo chmod -R a+rX /opt/mini-store
sudo chown www-data:www-data /var/lib/mini-store
sudo chmod 750 /var/lib/mini-store
```

Install and enable the Python service and Apache reverse proxy:

```bash
sudo cp deploy/systemd/mini-store.service /etc/systemd/system/mini-store.service
sudo cp deploy/apache/mini-store.conf /etc/apache2/sites-available/mini-store.conf
```

Edit `/etc/apache2/sites-available/mini-store.conf` and replace
`your-domain.example.com` with your domain. Enable Apache's proxy modules and
the new site, and disable the default site so it cannot list the repository:

```bash
sudo a2enmod proxy proxy_http
sudo a2dissite 000-default.conf
sudo a2ensite mini-store.conf
sudo systemctl daemon-reload
sudo systemctl enable --now mini-store
sudo apache2ctl configtest
sudo systemctl reload apache2
```

Point your domain to the VM and configure HTTPS before accepting sign-ins:
`SECURE_COOKIE=1` requires the browser to use HTTPS. For Let's Encrypt, install
Certbot and run `sudo certbot --apache -d your-domain.example.com`. Allow inbound
HTTP/HTTPS in the Azure network security group; do not expose port 8000.

The store starts with a fresh data file in `/var/lib/mini-store`. It does not
copy the sample accounts from the repository. Check the app and Apache logs
with `sudo journalctl -u mini-store` and
`sudo tail -f /var/log/apache2/mini-store-error.log`.

## First use

On the first run, the store asks you to create its first admin account. Save
that username and password; admin accounts can open the analytics screen.

After setup:

1. Choose **Sign up** to create a customer account, or **Sign in** if you
   already have one.
2. Choose **View catalogue** to see product IDs, prices, weights, and stock.
3. Choose **Add item to cart**, then enter a product ID and quantity.
4. Choose **View cart** to review your items.
5. Choose **Checkout and ship** and enter the recipient and address.
6. Choose **Shipment dashboard** to review your orders and shipping details.
7. Admins can choose **Admin analytics** to see store totals and create
   `admin_analytics.png`.

Shipping costs $5 per kilogram. Orders reduce the available product stock.

## Your store data

Accounts, products, orders, and shipments are saved in `store_data.json` in
this folder. Keep a backup of this file if you want to preserve your store
data. The store adds its starter products the first time it initializes.

## Project files

- `test.py` — starts the menus and handles user input.
- `web_server.py` and `web/` — serve the local browser storefront and its API.
- `user_service.py` and `user_model.py` — account creation and sign-in.
- `product_service.py` — product catalogue.
- `order_service.py` and `shipment_service.py` — checkout and shipments.
- `admin_service.py` and `visualization_service.py` — admin reports and chart.
- `database.py` — reads and saves the JSON store data.
- `requirements.txt` — chart libraries needed for admin analytics.

## Troubleshooting

- If `py` is not recognized, install Python and select **Add Python to PATH**
  during installation. You can also replace `py` with `python` in the commands.
- If the store reports a missing package, run the dependency-install command
  again from this folder.

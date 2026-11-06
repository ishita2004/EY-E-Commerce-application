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

## Deploy to an Azure Ubuntu VM with Nginx

Do not configure the repository as a public web root: that exposes source
files and checked-in sample data, and it does not run the Python API. For the
easiest install, SSH to the VM and paste this single command. It fetches the
app, starts the Python API, configures Nginx on port 90 to proxy requests, and
stops Apache if it was previously enabled:

```bash
set -o pipefail; curl -fsSL https://raw.githubusercontent.com/ishita2004/EY-E-Commerce-application/feature/inventory-value-report/deploy/install-nginx-ubuntu-vm.sh | sudo bash
```

Then allow inbound TCP port **90** in the Azure network security group and open
`http://<your-VM-public-IP>:90/`. Do not expose port 8000. This HTTP setup is
for testing only; configure HTTPS before accepting real passwords. The script
uses `SECURE_COOKIE=0` for HTTP testing. After setting up a domain and TLS,
change this to `SECURE_COOKIE=1` in
`/etc/systemd/system/mini-store.service` and restart the service:

```bash
sudo sed -i 's/SECURE_COOKIE=0/SECURE_COOKIE=1/' /etc/systemd/system/mini-store.service
sudo systemctl restart mini-store
```

For HTTPS, point a domain to the VM, allow inbound HTTP/HTTPS in the Azure
network security group, install Certbot, and configure its Nginx plugin.

The store starts with a fresh data file in `/var/lib/mini-store`. It does not
copy the sample accounts from the repository. Check app and Nginx logs with
`sudo journalctl -u mini-store` and `sudo tail -f /var/log/nginx/error.log`.

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

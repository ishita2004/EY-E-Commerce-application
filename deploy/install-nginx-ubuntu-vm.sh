#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_URL="https://github.com/ishita2004/EY-E-Commerce-application.git"
DEPLOY_BRANCH="feature/inventory-value-report"
APP_DIR="/opt/mini-store"
DATA_DIR="/var/lib/mini-store"
SERVICE_FILE="/etc/systemd/system/mini-store.service"
NGINX_SITE="/etc/nginx/sites-available/mini-store"
HTTP_PORT="${STORE_HTTP_PORT:-90}"

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this installer with sudo." >&2
    exit 1
fi

if ! [[ "${HTTP_PORT}" =~ ^[0-9]+$ ]] || (( HTTP_PORT < 1 || HTTP_PORT > 65535 )); then
    echo "STORE_HTTP_PORT must be a port number between 1 and 65535." >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y curl git nginx python3 python3-venv

if [[ -d "${APP_DIR}/.git" ]]; then
    git -C "${APP_DIR}" fetch origin "${DEPLOY_BRANCH}"
    git -C "${APP_DIR}" merge --ff-only FETCH_HEAD
elif [[ -e "${APP_DIR}" ]]; then
    echo "${APP_DIR} already exists and is not a Git checkout; move it before retrying." >&2
    exit 1
else
    git clone --depth 1 --branch "${DEPLOY_BRANCH}" "${REPOSITORY_URL}" "${APP_DIR}"
fi

python3 -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/pip" install --disable-pip-version-check -r "${APP_DIR}/requirements.txt"
chown -R root:root "${APP_DIR}"
chmod -R a+rX "${APP_DIR}"
install -d -o www-data -g www-data -m 0750 "${DATA_DIR}"

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Mini Store web application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
Environment=HOST=127.0.0.1
Environment=PORT=8000
Environment=STORE_DATA_PATH=${DATA_DIR}/store_data.json
Environment=SECURE_COOKIE=0
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/web_server.py
Restart=on-failure
RestartSec=3
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_DIR}

[Install]
WantedBy=multi-user.target
EOF

cat > "${NGINX_SITE}" <<EOF
server {
    listen ${HTTP_PORT} default_server;
    listen [::]:${HTTP_PORT} default_server;
    server_name _;
    server_tokens off;

    client_max_body_size 64k;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }
}
EOF

systemctl disable --now apache2 >/dev/null 2>&1 || true
rm -f /etc/nginx/sites-enabled/default
ln -sfn "${NGINX_SITE}" /etc/nginx/sites-enabled/mini-store
systemctl daemon-reload
systemctl enable --now mini-store

app_ready=0
for _ in {1..30}; do
    if curl --fail --silent http://127.0.0.1:8000/ >/dev/null; then
        app_ready=1
        break
    fi
    sleep 1
done
if [[ "${app_ready}" -ne 1 ]]; then
    systemctl status mini-store --no-pager || true
    echo "The Python app did not become ready; check: journalctl -u mini-store" >&2
    exit 1
fi

nginx -t
systemctl enable nginx
systemctl restart nginx
curl --fail --silent "http://127.0.0.1:${HTTP_PORT}/" >/dev/null

if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    ufw allow "${HTTP_PORT}/tcp"
fi

echo
echo "Mini Store is running with Nginx. Open http://<your-VM-public-IP>:${HTTP_PORT}/"
echo "Allow inbound TCP port ${HTTP_PORT} in the Azure network security group."
echo "Port 8000 is private. This HTTP setup is for testing only; configure HTTPS before using real passwords."
echo "App logs: sudo journalctl -u mini-store -f"
echo "Nginx logs: sudo tail -f /var/log/nginx/error.log"

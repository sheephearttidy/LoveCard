#!/bin/bash
# ============================================================
# LoveCards 宝塔面板一键部署脚本
# 使用方式：
#   1. 宝塔面板安装 Python 项目管理器
#   2. 将项目放到 /www/wwwroot/LoveCards
#   3. bash deploy/baota_setup.sh
# ============================================================

set -e

PROJECT_DIR="/www/wwwroot/LoveCards"
VENV_DIR="${PROJECT_DIR}/.venv"
PYTHON_VERSION="3.10"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

if [ ! -d "$PROJECT_DIR" ]; then
    error "项目目录不存在: $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# ---------- 1. Python 虚拟环境 ----------
if [ ! -d "$VENV_DIR" ]; then
    info "创建 Python 虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate

info "安装依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt
pip install gunicorn -q

# ---------- 2. 环境变量 ----------
if [ ! -f .env ]; then
    warn ".env 文件不存在，从 .env.example 复制"
    cp .env.example .env
    GENERATED_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/your-secret-key-here/${GENERATED_KEY}/" .env
    warn "已自动生成 SECRET_KEY，请编辑 .env 填写数据库密码："
    warn "  vi ${PROJECT_DIR}/.env"
    warn "填写完成后重新运行此脚本。"
    exit 0
fi

# ---------- 3. 数据库初始化 ----------
read -p "是否需要初始化数据库（建表+种子数据）？[y/N] " INIT_DB
if [[ "$INIT_DB" =~ ^[Yy]$ ]]; then
    info "初始化数据库..."
    python db_init.py reset
    warn "初始管理员: admin / admin，上线后务必修改密码！"
fi

# ---------- 4. 创建上传目录 ----------
mkdir -p uploads
chmod 755 uploads

# ---------- 5. Systemd 服务 ----------
info "创建 systemd 服务文件..."
cat > /etc/systemd/system/lovecard.service << EOF
[Unit]
Description=LoveCards Gunicorn Service
After=network.target mysql.service

[Service]
Type=notify
User=www
Group=www
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${VENV_DIR}/bin"
EnvironmentFile=${PROJECT_DIR}/.env
ExecStart=${VENV_DIR}/bin/gunicorn -c gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=30
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable lovecard

info "启动服务..."
systemctl start lovecard
sleep 2

if systemctl is-active --quiet lovecard; then
    info "LoveCards 服务已启动！"
else
    error "服务启动失败，请检查日志: journalctl -u lovecard -n 50"
fi

# ---------- 6. Nginx 配置 ----------
info "配置 Nginx..."
NGINX_CONF="/www/server/panel/vhost/nginx/lovecard.conf"

if [ ! -f "$NGINX_CONF" ]; then
    cp deploy/nginx.conf "$NGINX_CONF"
    warn "Nginx 配置已复制，请修改以下内容："
    warn "  1. server_name → 你的域名"
    warn "  2. ssl_certificate / ssl_certificate_key → SSL 证书路径"
    warn "  3. /uploads/ 和 /static/ 的 alias → 实际项目路径"
    warn ""
    warn "修改完成后执行: nginx -t && systemctl reload nginx"
else
    warn "Nginx 配置已存在，跳过。如需更新: cp deploy/nginx.conf $NGINX_CONF"
fi

# ---------- 完成 ----------
echo ""
info "=========================================="
info "  部署完成！"
info "=========================================="
echo ""
info "项目目录:   ${PROJECT_DIR}"
info "虚拟环境:   ${VENV_DIR}"
info "环境变量:   ${PROJECT_DIR}/.env"
info "服务状态:   systemctl status lovecard"
info "查看日志:   journalctl -u lovecard -f"
info "重启服务:   systemctl restart lovecard"
info "Nginx配置:  ${NGINX_CONF}"
echo ""
warn "后续步骤："
warn "  1. 编辑 .env 填写正确的数据库密码"
warn "  2. 修改 Nginx 配置中的域名和证书路径"
warn "  3. 在宝塔面板 SSL 页面申请证书"
warn "  4. 修改 admin 默认密码"
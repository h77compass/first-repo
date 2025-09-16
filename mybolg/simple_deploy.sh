#!/bin/bash
# 简化版Django博客部署脚本
# 使用前请修改下面的配置参数

# ====== 配置参数 ======
# 项目路径
PROJECT_DIR="/path/to/your/project/mybolg"
# 服务器IP
SERVER_IP="your_server_ip"
# 域名
DOMAIN="yourdomain.com"
# 数据库配置
DB_NAME="myblog_db"
DB_USER="db_user"
DB_PASSWORD="your_db_password"
# ====== 配置参数结束 ======

# 确保脚本以root权限运行
if [ "$EUID" -ne 0 ]
  then echo "请以root权限运行此脚本"
  exit
fi

# 更新系统包
apt update && apt upgrade -y

# 安装必要的软件
apt install -y python3 python3-pip python3-venv python3-dev nginx git mysql-server mysql-client libmysqlclient-dev

# 配置MySQL
mysql -e "CREATE DATABASE ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';"
mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# 克隆项目代码（如果还没有）
if [ ! -d "$PROJECT_DIR" ]; then
    git clone your_repository_url "$PROJECT_DIR"
fi

# 创建虚拟环境
python3 -m venv "$PROJECT_DIR/venv"

# 激活虚拟环境并安装依赖
source "$PROJECT_DIR/venv/bin/activate"
pip install --upgrade pip
pip install django gunicorn pymysql mysqlclient

# 修改settings.py文件
sed -i "s/DEBUG = True/DEBUG = False/g" "$PROJECT_DIR/myblog_project/settings.py"
sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = ['${DOMAIN}', 'www.${DOMAIN}', '${SERVER_IP}']/g" "$PROJECT_DIR/myblog_project/settings.py"
sed -i "/STATIC_URL = 'static'/a STATIC_ROOT = BASE_DIR / 'staticfiles'" "$PROJECT_DIR/myblog_project/settings.py"
sed -i "/STATIC_ROOT = BASE_DIR \/ 'staticfiles'/a MEDIA_URL = '/media/'\nMEDIA_ROOT = BASE_DIR / 'media'" "$PROJECT_DIR/myblog_project/settings.py"

# 修改数据库配置
sed -i "/DATABASES = {/,/}/c\DATABASES = {\n    'default': {\n        'ENGINE': 'django.db.backends.mysql',\n        'NAME': '${DB_NAME}',\n        'USER': '${DB_USER}',\n        'PASSWORD': '${DB_PASSWORD}',\n        'HOST': 'localhost',\n        'PORT': '3306',\n        'OPTIONS': {\n            'charset': 'utf8mb4',\n        },\n    }\n}" "$PROJECT_DIR/myblog_project/settings.py"

# 在__init__.py中配置PyMySQL
echo "import pymysql\npymysql.install_as_MySQLdb()" > "$PROJECT_DIR/myblog_project/__init__.py"

# 运行数据库迁移
cd "$PROJECT_DIR"
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 创建超级用户
python manage.py createsuperuser --username admin --email admin@example.com --noinput

# 设置超级用户密码
python -c "import os\nos.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myblog_project.settings')\nimport django\ndjango.setup()\nfrom django.contrib.auth import get_user_model\nUser = get_user_model()\nuser = User.objects.get(username='admin')\nuser.set_password('admin123')\nuser.save()"

# 创建Gunicorn服务文件
cat > /etc/systemd/system/gunicorn.service << EOL
[Unit]
Description=gunicorn daemon for myblog
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:${PROJECT_DIR}/myblog.sock myblog_project.wsgi:application

[Install]
WantedBy=multi-user.target
EOL

# 启动Gunicorn服务
systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn

# 创建Nginx配置文件
cat > /etc/nginx/sites-available/myblog << EOL
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN} ${SERVER_IP};

    location = /favicon.ico { access_log off; log_not_found off; }
    
    # 静态文件配置
    location /static/ {
        root ${PROJECT_DIR};
    }
    
    # 媒体文件配置
    location /media/ {
        root ${PROJECT_DIR};
    }
    
    # 动态请求转发给Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:${PROJECT_DIR}/myblog.sock;
    }
}
EOL

# 启用Nginx配置
ln -s /etc/nginx/sites-available/myblog /etc/nginx/sites-enabled/

# 测试Nginx配置
nginx -t

# 重启Nginx
systemctl restart nginx

# 安装Certbot（用于获取SSL证书）
apt install -y certbot python3-certbot-nginx

# 提示用户完成后续步骤
echo ""
echo "========================================================================="
echo "基础部署已完成！接下来您需要手动完成以下步骤："
echo "1. 将您的域名(${DOMAIN})解析到服务器IP(${SERVER_IP})"
echo "2. 运行 'certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}' 配置SSL证书"
echo "3. 登录管理后台(${DOMAIN}/admin)修改超级用户密码(当前密码: admin123)"
echo "4. 检查网站运行状态，根据需要调整配置"
echo "========================================================================="
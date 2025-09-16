# Django博客部署指南

本指南将详细说明如何将您的Django博客部署到生产环境，使其他人可以通过互联网访问您的博客。

## 目录
1. [准备工作](#准备工作)
2. [选择部署平台](#选择部署平台)
3. [生产环境配置](#生产环境配置)
4. [安装依赖](#安装依赖)
5. [数据库迁移](#数据库迁移)
6. [配置静态文件](#配置静态文件)
7. [设置Gunicorn应用服务器](#设置-gunicorn-应用服务器)
8. [配置Nginx作为反向代理](#配置-nginx-作为反向代理)
9. [域名绑定](#域名绑定)
10. [SSL证书配置](#ssl-证书配置)
11. [自动化部署(可选)](#自动化部署可选)
12. [部署后维护](#部署后维护)

## 准备工作

在开始部署之前，您需要准备以下内容：

1. 一个域名（可以从阿里云、腾讯云、Godaddy等域名注册商购买）
2. 一个VPS或云服务器（推荐使用Ubuntu 20.04或更高版本）
3. 服务器的SSH访问权限
4. 基本的Linux命令知识

## 选择部署平台

您可以选择以下几种常见的部署方式：

1. **VPS/云服务器**：如阿里云ECS、腾讯云CVM、AWS EC2等，完全控制服务器环境
2. **PaaS平台**：如Heroku、PythonAnywhere、 Railway等，简化部署流程但灵活性较低
3. **容器化部署**：使用Docker和Docker Compose，便于环境一致性管理

本指南主要针对VPS/云服务器部署方式进行说明。

## 生产环境配置

### 1. 修改settings.py文件

首先，需要修改`myblog_project/settings.py`文件，调整以下设置：

```python
# 将DEBUG模式关闭
DEBUG = False

# 添加您的域名到ALLOWED_HOSTS
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# 设置静态文件根目录
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 配置媒体文件存储
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 配置数据库（如果使用MySQL或PostgreSQL）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'myblog_db',
        'USER': 'db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# 配置日志系统
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# 配置安全性相关设置
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 2. 创建requirements.txt文件

在项目根目录创建`requirements.txt`文件，列出所有依赖：

```bash
pip freeze > requirements.txt
```

## 安装依赖

在您的服务器上，执行以下命令安装所需依赖：

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装Python和相关工具
sudo apt install python3 python3-pip python3-venv python3-dev -y

# 安装数据库（如果使用MySQL）
sudo apt install mysql-server mysql-client libmysqlclient-dev -y

# 安装Nginx
sudo apt install nginx -y

# 安装Git
sudo apt install git -y
```

## 数据库迁移

如果您使用MySQL或PostgreSQL作为生产数据库，需要创建数据库和用户：

### MySQL示例：

```bash
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE myblog_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建数据库用户并授权
CREATE USER 'db_user'@'localhost' IDENTIFIED BY 'your_db_password';
GRANT ALL PRIVILEGES ON myblog_db.* TO 'db_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

然后运行Django的迁移命令：

```bash
python manage.py migrate
```

## 配置静态文件

在生产环境中，Django不会自动处理静态文件，需要使用`collectstatic`命令收集所有静态文件：

```bash
python manage.py collectstatic
```

这将把所有静态文件复制到`STATIC_ROOT`指定的目录中。

## 设置Gunicorn应用服务器

Gunicorn是一个WSGI HTTP服务器，用于运行Django应用：

### 安装Gunicorn

```bash
pip install gunicorn
```

### 测试Gunicorn

```bash
gunicorn --bind 0.0.0.0:8000 myblog_project.wsgi:application
```

如果一切正常，您应该能够通过服务器IP地址和8000端口访问您的网站。

### 创建Gunicorn Systemd服务文件

为了让Gunicorn能够在系统启动时自动运行，创建一个Systemd服务文件：

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

添加以下内容：

```ini
[Unit]
Description=gunicorn daemon for myblog
After=network.target

[Service]
User=your_user
Group=www-data
WorkingDirectory=/path/to/your/project/mybolg
ExecStart=/path/to/your/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/path/to/your/project/mybolg/myblog.sock myblog_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

替换上面的路径和用户名为您的实际值。

启动并启用Gunicorn服务：

```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 配置Nginx作为反向代理

Nginx将作为前端服务器，处理静态文件请求并将动态请求转发给Gunicorn：

### 创建Nginx配置文件

```bash
sudo nano /etc/nginx/sites-available/myblog
```

添加以下内容：

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    # 静态文件配置
    location /static/ {
        root /path/to/your/project/mybolg;
    }
    
    # 媒体文件配置
    location /media/ {
        root /path/to/your/project/mybolg;
    }
    
    # 动态请求转发给Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/your/project/mybolg/myblog.sock;
    }
}
```

替换上面的路径和域名。

### 启用Nginx配置

```bash
sudo ln -s /etc/nginx/sites-available/myblog /etc/nginx/sites-enabled/

# 测试Nginx配置是否正确
sudo nginx -t

# 重启Nginx服务
sudo systemctl restart nginx
```

## 域名绑定

要让用户能够通过域名访问您的博客，需要将域名指向您的服务器IP地址：

1. 登录您的域名注册商网站
2. 找到DNS管理或域名解析设置
3. 添加两条A记录：
   - 主机记录: `@` 指向您的服务器IP地址
   - 主机记录: `www` 指向您的服务器IP地址
4. 保存设置，等待DNS解析生效（通常需要几分钟到几小时）

## SSL证书配置

为了提供HTTPS安全访问，建议配置SSL证书：

### 使用Let's Encrypt获取免费SSL证书

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取并安装SSL证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 设置自动续期
sudo certbot renew --dry-run
```

Certbot会自动修改Nginx配置以启用HTTPS。

## 自动化部署(可选)

对于频繁更新的博客，您可以设置自动化部署流程：

### 创建部署脚本

```bash
#!/bin/bash
# deploy.sh

# 设置项目路径
PROJECT_PATH="/path/to/your/project/mybolg"
VENV_PATH="/path/to/your/venv"

# 切换到项目目录
cd $PROJECT_PATH

# 拉取最新代码
git pull origin main

# 激活虚拟环境
source $VENV_PATH/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 重启Gunicorn服务
sudo systemctl restart gunicorn

# 重启Nginx服务
sudo systemctl restart nginx

# 退出虚拟环境
deactivate
```

使脚本可执行：

```bash
chmod +x deploy.sh
```

### 使用Git钩子或CI/CD工具

您也可以设置Git钩子或使用CI/CD工具（如GitHub Actions、Jenkins等）实现更复杂的自动化部署流程。

## 部署后维护

### 定期备份

设置定期备份数据库和重要文件：

```bash
# 备份数据库
mysqldump -u db_user -p myblog_db > backup.sql

# 备份整个项目目录
tar -czvf myblog_backup.tar.gz /path/to/your/project/mybolg
```

### 监控日志

定期检查日志文件，及时发现和解决问题：

```bash
# 查看Nginx访问日志
sudo tail -f /var/log/nginx/access.log

# 查看Nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 查看Gunicorn日志
sudo journalctl -u gunicorn

# 查看Django应用日志
tail -f /path/to/your/project/mybolg/django.log
```

### 定期更新

定期更新系统和项目依赖：

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 更新项目依赖
pip install --upgrade -r requirements.txt
```

---

通过以上步骤，您应该能够成功将Django博客部署到域名上，使其他人可以通过互联网访问。如果在部署过程中遇到任何问题，请参考相关文档或寻求社区支持。
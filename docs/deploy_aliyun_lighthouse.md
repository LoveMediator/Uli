# Uli 阿里云轻量服务器部署指南

本文档按“最快稳定上线”设计，推荐方案：

- 前端：Vite build 后的静态文件
- 后端：FastAPI + Uvicorn
- 反向代理：Nginx
- 数据库：PostgreSQL
- 缓存：Redis
- 进程托管：systemd

这套方案最适合当前仓库，因为前端生产环境默认请求 `/api/v1`，和 Nginx 同域反代天然匹配。

## 1. 推荐服务器规格

- 系统：Ubuntu 22.04 LTS
- 配置：2C2G 起步
- 安全组开放端口：
  - `22` SSH
  - `80` HTTP
  - `443` HTTPS

如果暂时没有域名，也可以先用公网 IP 部署，但正式使用仍建议绑定域名并上 HTTPS。

## 2. 服务器初始化

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y nginx redis-server postgresql postgresql-contrib python3 python3-venv python3-pip git
```

确认服务：

```bash
sudo systemctl enable nginx redis-server postgresql
sudo systemctl start nginx redis-server postgresql
sudo systemctl status nginx --no-pager
sudo systemctl status redis-server --no-pager
sudo systemctl status postgresql --no-pager
```

## 3. 拉取项目

建议统一放到 `/srv`：

```bash
sudo mkdir -p /srv
sudo chown -R $USER:$USER /srv
cd /srv
git clone <你的仓库地址> LoveMediator
cd /srv/LoveMediator
```

## 4. 配置 PostgreSQL

进入 postgres：

```bash
sudo -u postgres psql
```

执行：

```sql
CREATE USER uli WITH PASSWORD '替换成强密码';
CREATE DATABASE uli_prod OWNER uli;
GRANT ALL PRIVILEGES ON DATABASE uli_prod TO uli;
\q
```

## 5. 配置后端环境变量

进入后端目录：

```bash
cd /srv/LoveMediator/backend
cp .env.example .env
```

将 `.env` 改成生产配置，至少保证这些值正确：

```env
DEBUG=false
DATABASE_URL=postgresql+psycopg://uli:你的数据库密码@127.0.0.1:5432/uli_prod
REDIS_URL=redis://127.0.0.1:6379/0
SECRET_KEY=替换成长度足够的随机字符串
CORS_ORIGINS=https://你的域名
LLM_PROVIDER=xiaomi
LLM_API_KEY=你的小米中转站密钥
LLM_BASE_URL=http://47.113.229.93:3009/v1
LLM_TEXT_MODEL=mimo-v2.5-pro
LLM_VISION_MODEL=mimo-v2-omni
LLM_AUTH_SCHEME=bearer
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

注意：

- `DEBUG` 必须是 `false`
- `SECRET_KEY` 必须固定，不能每次重启变化
- 如果暂时用公网 IP 访问，把 `CORS_ORIGINS` 改成 `http://你的公网IP`
- 当前模型调用走小米中转站，`LLM_BASE_URL` 需要保留 `/v1` 后缀，`LLM_AUTH_SCHEME` 使用 `bearer`

## 6. 安装后端并迁移数据库

```bash
cd /srv/LoveMediator/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
python -m alembic upgrade head
python -m alembic current
```

## 7. 启动后端自检

先手动跑一遍：

```bash
cd /srv/LoveMediator/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
```

新开一个终端测试：

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/ready
```

如果 `ready` 返回 200，说明数据库连通正常。

## 8. 构建前端

```bash
cd /srv/LoveMediator/fontend
npm install
npm run build
```

当前前端生产配置已经适合“同域名 + `/api` 反代”模式，不需要额外改 API 地址。

## 9. systemd 托管后端

把仓库内模板复制到 systemd：

```bash
sudo cp /srv/LoveMediator/deploy/aliyun/uli-backend.service /etc/systemd/system/uli-backend.service
```

如有需要，先编辑其中的路径和用户，然后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl enable uli-backend
sudo systemctl restart uli-backend
sudo systemctl status uli-backend --no-pager
journalctl -u uli-backend -n 100 --no-pager
```

## 10. Nginx 反向代理

复制模板：

```bash
sudo cp /srv/LoveMediator/deploy/aliyun/uli-nginx.conf /etc/nginx/sites-available/uli
```

编辑以下占位内容：

- `server_name`
- `root`
- SSL 证书路径（如果已经有证书）

启用站点：

```bash
sudo ln -sf /etc/nginx/sites-available/uli /etc/nginx/sites-enabled/uli
sudo nginx -t
sudo systemctl reload nginx
```

## 11. HTTPS

如果域名已经解析到服务器，推荐用 Certbot：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名
```

完成后再次检查：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 12. 验收清单

- `curl http://127.0.0.1:8000/health` 返回 200
- `curl http://127.0.0.1:8000/health/ready` 返回 200
- 浏览器访问首页正常
- 注册 / 登录正常
- 关系绑定可创建邀请码、可接受邀请码
- 调解室可创建分析会话
- 日历日期无错位
- 小精灵接口调用正常

## 13. 当前仓库上线注意点

- 当前仓库更适合非 Docker 方式快速上线
- `backend/Dockerfile` 还是空的，不建议今天临时走容器化
- 前端使用相对 API 地址 `/api/v1`，所以 Nginx 同域代理是最省事的
- 本次修复不包含 schema 变更，不需要新增 migration

## 14. 回滚建议

更新前先备份：

```bash
cp /srv/LoveMediator/backend/.env /srv/LoveMediator/backend/.env.bak
```

代码回滚：

```bash
cd /srv/LoveMediator
git log --oneline -n 5
git checkout <上一个稳定提交>
```

然后：

```bash
sudo systemctl restart uli-backend
sudo systemctl reload nginx
```

# Docker 部署说明

这套项目现在适合用 `Docker Compose` 部署，结构已经按下面这套方式准备好了：

- `app`：FastAPI + 智能体后端
- `redis`：缓存和上下文存储
- `server/runtime`：持久化 SQLite
- `logs`：运行日志

## 1. 服务器准备

推荐云服务器配置：

- 2 核 4G 起步
- Ubuntu 22.04 / 24.04
- 开放端口：`22`、`80`、`443`，测试阶段至少开放 `8000`

安装 Docker 和 Compose：

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

## 2. 上传项目

本地提交代码后，在服务器拉取：

```bash
git clone https://github.com/BeiGuaiQian/programming_education_system.git
cd programming_education_system/programming_edu_sys
```

如果你的仓库根目录本身就是 `programming_edu_sys`，那就直接：

```bash
git clone https://github.com/BeiGuaiQian/programming_education_system.git
cd programming_education_system
```

## 3. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
mkdir -p server/runtime logs
```

至少改这些值：

```env
DEEPSEEK_API_KEY=你的真实key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

USE_REDIS=true
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

SERVER_ADMIN_USERNAME=admin
SERVER_ADMIN_PASSWORD=改成强密码
SERVER_TOKEN_EXPIRE_MINUTES=120
SERVER_REFRESH_TOKEN_EXPIRE_DAYS=14
SERVER_APP_DB=/app/server/runtime/app.db
SERVER_WORKERS=1

LOG_FILE=/app/logs/system.log
```

如果你暂时不想启用 Redis，也可以设成：

```env
USE_REDIS=false
```

但既然是服务器部署，我更建议保留 Redis。

## 4. 启动服务

首次构建并启动：

```bash
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
docker compose logs -f app
```

浏览器访问：

```text
http://你的服务器公网IP:8000/
```

## 5. 更新项目

后续更新代码时：

```bash
git pull
docker compose up -d --build
```

## 6. 持久化说明

下面这些数据不会因为容器重建而丢失：

- `./server/runtime`：用户、会话、学习记录 SQLite
- `./logs`：系统日志
- `redis-data`：Redis 持久化卷

## 7. 生产环境建议

正式上线时，不建议直接暴露 `8000`，更推荐：

1. 用 Nginx 或 Caddy 反向代理到 `app:8000`
2. 绑定域名
3. 配 HTTPS
4. 只对外开放 `80/443`

如果你只是先测试，可以先直接访问 `8000`。

## 8. 进阶建议

- `SERVER_WORKERS`
  - 2 核机器先用 `1`
  - 4 核机器可以尝试 `2`
- 服务器内存不高时，先不要开太多 worker
- SQLite 适合你当前阶段；如果之后并发和写入明显上升，再切 PostgreSQL

## 9. 常用命令

重启：

```bash
docker compose restart
```

停止：

```bash
docker compose down
```

查看 app 日志：

```bash
docker compose logs -f app
```

进入容器：

```bash
docker compose exec app bash
```

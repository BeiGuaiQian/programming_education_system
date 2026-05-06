# 云服务器部署快速说明

## 推荐服务器

- 2 核 CPU
- 4 GB 内存
- 40 GB 以上 SSD
- Ubuntu 22.04 / 24.04
- 5 Mbps 以上公网带宽

5 个左右并发访问时，这个配置足够用于结项展示和小范围试用。

## 1. 上传项目

将整个 `programming_edu_sys_deploy` 目录上传到服务器，例如：

```bash
/opt/programming_edu_sys
```

## 2. 配置环境变量

进入项目目录：

```bash
cd /opt/programming_edu_sys
cp .env.production.example .env
```

编辑 `.env`，至少修改：

```env
DEEPSEEK_API_KEY=你的真实API_KEY
SERVER_ADMIN_PASSWORD=一个安全密码
```

如果暂时没有大模型 Key，系统仍可启动，但智能回答会降级为基础提示。

## 3. 启动服务

```bash
docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f app
```

访问：

```text
http://服务器公网IP:8000/
```

## 4. 常用命令

重启：

```bash
docker compose restart
```

停止：

```bash
docker compose down
```

更新代码后重新构建：

```bash
docker compose up -d --build
```

## 5. 安全组

服务器安全组至少开放：

- `8000`：临时演示访问
- `22`：SSH

如果后续配置 Nginx 和域名，再开放：

- `80`
- `443`

## 6. 注意事项

- 不要把真实 `.env` 提交到 Git 或发给无关人员。
- `server/runtime` 是运行时数据库目录，服务器上会自动生成数据文件。
- `logs` 是日志目录，出现问题时优先查看 `docker compose logs -f app`。
- 目前 SQLite 足够支撑小范围试用；如果后续多人长期使用，再考虑迁移到 PostgreSQL 或 MySQL。

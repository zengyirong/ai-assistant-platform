# AI Assistant Platform Docker 上线执行文档

本文档用于把 AI Assistant Platform 从 0-1 部署到 Ubuntu 服务器。部署方式为：宿主机 Nginx 负责公网入口和 HTTPS，本项目用 Docker Compose 独立运行前端、后端、MySQL、Qdrant，只暴露本机回环端口，尽量不影响服务器上已有的非 Docker 项目。

仓库已包含生产文件，**无需现场手写**：

| 文件 | 用途 |
|---|---|
| `docker-compose.prod.yml` | 生产 Compose（含 mem/cpu 限额） |
| `backend/Dockerfile` | 后端镜像 |
| `frontend/scripts/deploy/Dockerfile.prod` | 前端生产镜像（构建 `web-ele`） |
| `frontend/scripts/deploy/nginx.prod.conf` | 前端容器内 Nginx |
| `.env.prod.example` | 生产环境变量模板 |

## 0. 上线前前置条件（真正的 0）

开始第 1 节之前，先确认下列事项全部满足。缺任何一项都会导致「容器起来了但外网打不开」。

### 0.1 必备清单

- [ ] 已有云服务器（推荐 Ubuntu 22.04），能 SSH 登录，当前用户有 `sudo`
- [ ] 已有域名，并已解析到服务器公网 IP（A 记录）
- [ ] 云厂商安全组入方向放行：`22`（SSH）、`80`、`443`
- [ ] 服务器本机防火墙若启用，同样放行 `80`/`443`（本项目 Docker **不**映射公网端口）
- [ ] 宿主机已安装或可安装 Nginx（公网入口由宿主机 Nginx 接管，不要让 Docker 抢 80/443）
- [ ] 已记录服务器上**已有项目**的域名与访问方式，部署前后各测一次

域名与证书细则见：[docs/https-deploy-runbook.md](docs/https-deploy-runbook.md)（阿里云 DNS / 安全组 / 证书可复用）。

### 0.2 快速自检

在你自己的电脑上：

```bash
ping 你的域名
# 应解析到 ECS 公网 IP
```

在服务器上：

```bash
curl -I http://127.0.0.1/   # 或已有站点域名，确认原有 Nginx 正常
ss -tulpn | grep -E ':80|:443'
```

### 0.3 若尚未安装 Nginx

```bash
sudo apt-get update
sudo apt-get install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
sudo nginx -t
```

## 1. 部署目标与服务器约束

### 1.1 当前服务器信息

- CPU：2 核 vCPU
- 内存：4 GiB
- 操作系统：Ubuntu 22.04 64 位
- 服务器已有其他项目，并且已有项目不是 Docker 部署
- 服务器公网入口预计已有 Nginx，占用 80/443

### 1.2 本项目部署定位

- 适合：MVP、内部试用、小规模用户、小规模知识库、小并发 RAG 查询。
- 暂不适合：高并发问答、大量文档批量导入、大规模向量检索、在服务器上同时跑前端镜像构建。
- 后续升级建议：内存长期 >80%、Qdrant 变慢、文档导入频繁失败或挤压已有项目时，优先升到 4 核 8G，或把 MySQL/Qdrant 拆到独立机器/云服务。

### 1.3 内存账本（2C4G 共部署必看）

容器限额合计约 **2.6G**，但 4G 机器还要给 OS 和已有项目留空：

| 用途 | 建议预留 | 说明 |
|---|---:|---|
| 宿主机 OS + SSH + 宿主机 Nginx | ≥ 0.6G | 不可挤占 |
| 已有非 Docker 项目 | 按实测算 | 部署前用 `free -h` / 业务进程内存估算 |
| MySQL 容器 | 1.0G | `mem_limit` + `innodb-buffer-pool-size=256M` |
| Qdrant 容器 | 1.0G | 向量与索引 |
| Backend 容器 | 0.5G | PDF/DOCX 解析吃紧时可提到 768M |
| Frontend 容器 | 0.13G | 仅静态 Nginx |
| **合计（本项目）** | **~2.6G** | 不含构建峰值 |

硬性结论：

1. 若「已有项目 + OS」已占用 ≥1.2G，本项目上 2C4G **偏紧**，建议先升配或拆库。
2. **2C4G 默认不要在服务器上 `docker compose build` 前端**，改用第 12 节「本地构建 + 上传镜像」。
3. 建议配置 1～2G swap，避免偶发尖峰把已有项目打挂（见 2.1）。

### 1.4 部署架构

```text
用户浏览器
  |
  | HTTPS / 域名
  v
宿主机 Nginx（已有，继续管理 80/443）
  |-- /              -> 127.0.0.1:18080 -> frontend 容器 Nginx
  |-- /api/v1/*      -> 127.0.0.1:18000 -> backend 容器 FastAPI
  |-- /health /ready -> 127.0.0.1:18000 -> backend 容器 FastAPI

Docker Compose 项目网络 aap_net
  |-- frontend
  |-- backend
  |-- mysql
  |-- qdrant

Docker volumes
  |-- aap_mysql_data
  |-- aap_qdrant_data
  |-- aap_backend_files
```

### 1.5 端口规划

| 组件 | 端口 | 暴露范围 | 说明 |
|---|---:|---|---|
| 宿主机 Nginx | 80/443 | 公网 | 已有入口，不被 Docker 接管 |
| frontend | 127.0.0.1:18080 | 仅本机 | 静态前端，由宿主机 Nginx 反代 |
| backend | 127.0.0.1:18000 | 仅本机 | FastAPI，由宿主机 Nginx 反代 |
| mysql | 不映射公网 | Docker 内网 | 仅 backend 访问 |
| qdrant | 不映射公网 | Docker 内网 | 仅 backend 访问 |

## 2. 上线前检查

登录服务器后，先做基线检查，确认不会撞端口、不会挤爆磁盘。

```bash
free -h
df -h
ss -tulpn
nginx -t
systemctl status nginx --no-pager
```

重点确认：

- `80/443` 由宿主机 Nginx 占用。
- `127.0.0.1:18080` 和 `127.0.0.1:18000` 没有被占用。
- 磁盘剩余空间建议至少 **15G**（镜像 + volume + 备份；MVP 最小 10G）。
- 内存：用 1.3 节账本估算后，空闲建议 ≥1G。
- 已有项目在部署前访问正常，记录域名和访问结果。

如果端口被占用，把本文档与 `docker-compose.prod.yml` 中的 `18080`、`18000` 改成其他未占用端口，并同步修改 Nginx 反代配置。

### 2.1 建议配置 swap（2C4G）

```bash
# 若尚未有 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## 3. 安装基础软件

### 3.1 安装 Docker 和 Compose

如果服务器已经安装 Docker，可跳过安装，只检查版本。

```bash
docker --version
docker compose version
```

Ubuntu 22.04 可使用 Docker 官方源安装：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

启动 Docker：

```bash
sudo systemctl enable docker
sudo systemctl start docker
docker --version
docker compose version
```

如果希望当前用户免 `sudo` 执行 Docker：

```bash
sudo usermod -aG docker $USER
```

执行后需要退出 SSH 重新登录。

说明：本项目端口只绑 `127.0.0.1`，不依赖 Docker 发布公网端口。若服务器启用了 UFW，仍请确认 `80/443` 对公网放行（给宿主机 Nginx 用）。

### 3.2 安装 Git

```bash
sudo apt-get install -y git
git --version
```

## 4. 准备项目目录

建议统一放到 `/opt/aap`。

```bash
sudo mkdir -p /opt/aap
sudo chown -R $USER:$USER /opt/aap
cd /opt/aap
```

拉取代码：

```bash
git clone <你的仓库地址> ai-assistant-platform
cd ai-assistant-platform
```

如果不是 Git 仓库部署，也可以上传项目压缩包到 `/opt/aap/ai-assistant-platform`，但后续升级会不如 Git 方便。

确认生产文件存在：

```bash
ls docker-compose.prod.yml backend/Dockerfile frontend/scripts/deploy/Dockerfile.prod .env.prod.example
```

## 5. 配置生产环境变量

### 5.1 创建 `.env.prod`

```bash
cp .env.prod.example .env.prod
nano .env.prod
```

必须替换：

- `APP_SECRET`（至少 32 位随机串）
- `MYSQL_PASSWORD`、`MYSQL_ROOT_PASSWORD`
- `LLM_API_KEY`、`EMBEDDING_API_KEY`（真实上线时）
- `CORS_ORIGINS`，例如 `["https://aap.example.com"]`

注意：

- 离线试跑可把 `LLM_PROVIDER` / `EMBEDDING_PROVIDER` 设为 `fake`；真实 RAG 必须改回 `openai_compatible`（或你的兼容网关）。
- `EMBEDDING_DIMENSION` 一旦和 Qdrant collection 建好后绑定，换模型维度需新建 collection 并重建索引。
- `FILE_STORAGE_PATH` 生产保持 `/app/data/files`（对应 Compose volume）。
- **不要**对整个 `.env.prod` 执行 `source`：`CORS_ORIGINS=[...]` 会让 bash 报错。需要密码时只 `export` 单个变量（见第 8、15 节）。

### 5.2 前端 API 地址

`frontend/scripts/deploy/Dockerfile.prod` 构建时会写入：

```env
VITE_GLOB_API_URL=/api/v1
```

一般**不必**再手改 `frontend/apps/web-ele/.env.production`。若你改了 Dockerfile 或本地直接 `pnpm build:ele`，请自行保证生产值为 `/api/v1`，不要保留 `https://mock-napi.vben.pro/api`。

### 5.3 Compose 资源限额说明

`docker-compose.prod.yml` 已设置：

| 服务 | mem_limit | cpus | 其他 |
|---|---:|---:|---|
| mysql | 1g | 0.75 | buffer pool 256M，max-connections 80 |
| qdrant | 1g | 0.50 | |
| backend | 512m | 0.50 | uvicorn workers=1 |
| frontend | 128m | 0.25 | |

上传/解析大 PDF 若导致 backend 重启，可把 backend `mem_limit` 调到 `768m`，并用 `docker stats` 观察是否挤压已有项目。

## 6. 构建策略选择

| 场景 | 建议 |
|---|---|
| 2C4G 且已有其他项目 | **默认走第 12 节**：本地/大机器构建，上传 `aap-images.tar` |
| ≥4 核 8G，低峰期 | 可在服务器执行第 7 节 `build` |
| 仅改后端、前端镜像已有 | 可只 `build backend` |

## 7. 构建与启动（服务器内存充足时）

2C4G 共部署请跳过本节 build，直接用第 12 节导入镜像后从「启动服务」继续。

### 7.1 校验 Compose

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod config
```

如果这里报错，先修复环境变量或 YAML 格式。

### 7.2 构建镜像

建议低峰期执行，并另开终端观察 `free -h`。

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod build
```

若 OOM 或服务器卡死：立刻停构建，改走第 12 节。

### 7.3 启动服务

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

查看状态：

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
docker logs --tail=100 aap-backend
docker logs --tail=100 aap-frontend
```

## 8. 初始化数据库

### 8.1 执行 Alembic 迁移

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend alembic upgrade head
```

必须通过 `docker compose exec backend` 执行，以便使用 Compose 注入的环境变量。不要在宿主机 `backend/` 目录裸跑 alembic。

### 8.2 导入基础种子数据

只导出备份/导入需要的变量（不要 `source .env.prod`）：

```bash
export MYSQL_ROOT_PASSWORD='你的MySQL root密码'
export MYSQL_DATABASE='ai_assistant'
```

再导入：

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T mysql \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" < docs/mysql/seed_v1.sql
```

`docs/mysql/seed_v1.sql` 通过宿主机 shell 重定向进入容器，不必事先拷进 MySQL 容器。

### 8.3 初始化菜单权限

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend \
  python scripts/seed_menus.py
```

### 8.4 重启后端

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod restart backend
```

## 9. 本机健康检查

在服务器上执行：

```bash
curl -i http://127.0.0.1:18000/health
curl -i http://127.0.0.1:18000/ready
curl -I http://127.0.0.1:18080/
```

期望：

- `/health` 返回 200。
- `/ready` 返回 200，并显示 MySQL/Qdrant 都是 `ok`。
- 前端返回 200 或 304。

如果 `/ready` 失败：

```bash
docker logs --tail=200 aap-backend
docker logs --tail=200 aap-mysql
docker logs --tail=200 aap-qdrant
```

常见原因：

- `.env.prod` 中 MySQL 密码不一致。
- MySQL 首次启动还没完成初始化（等 health 变 healthy 再迁库）。
- `QDRANT_URL` 没有写成 `http://qdrant:6333`。
- 后端容器没有和依赖服务在同一个 Docker network。

## 10. 配置宿主机 Nginx 反代

假设域名是 `aap.example.com`，创建：

```bash
sudo nano /etc/nginx/sites-available/aap.example.com.conf
```

写入：

```nginx
server {
    listen 80;
    server_name aap.example.com;

    client_max_body_size 25m;

    location /api/v1/ {
        proxy_pass http://127.0.0.1:18000/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    location = /health {
        proxy_pass http://127.0.0.1:18000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /ready {
        proxy_pass http://127.0.0.1:18000/ready;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/aap.example.com.conf /etc/nginx/sites-enabled/aap.example.com.conf
sudo nginx -t
sudo systemctl reload nginx
```

先验证 HTTP：

```bash
curl -I http://aap.example.com/
curl -i http://aap.example.com/health
curl -i http://aap.example.com/ready
```

同时再测一遍**已有项目**域名，确认未被影响。

## 11. 配置 HTTPS

如果服务器已有 HTTPS 和证书管理方式，沿用现有方式即可；步骤可参考 [docs/https-deploy-runbook.md](docs/https-deploy-runbook.md)。

若使用 Certbot：

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d aap.example.com
```

验证自动续期：

```bash
sudo certbot renew --dry-run
```

HTTPS 完成后，确认 `.env.prod`：

```env
CORS_ORIGINS=["https://aap.example.com"]
```

然后重启后端：

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod restart backend
```

## 12. 2C4G 默认推荐：本地构建并上传镜像

在**内存充足的本机或构建机**上（需已安装 Docker，且项目目录含 `docker-compose.prod.yml`）：

```bash
# 可用一份仅含构建无关占位符的 .env.prod，或直接用服务器将要上线的那份（勿把真实密钥提交到 Git）
docker compose -f docker-compose.prod.yml --env-file .env.prod build frontend backend
docker save aap-frontend:prod aap-backend:prod -o aap-images.tar
```

上传到服务器：

```bash
scp aap-images.tar 用户名@服务器IP:/opt/aap/
```

服务器导入并启动（MySQL/Qdrant 仍由 Compose 拉官方镜像）：

```bash
cd /opt/aap
docker load -i aap-images.tar
cd /opt/aap/ai-assistant-platform
# 确保 .env.prod 已按第 5 节配置
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

然后从第 8 节继续做数据库初始化。

Compose 已显式指定 `image: aap-frontend:prod` / `aap-backend:prod`，与 `docker save` 名称一致。

## 13. 上线验收清单

### 13.1 服务验收

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
curl -i https://aap.example.com/health
curl -i https://aap.example.com/ready
```

浏览器访问：

- `https://aap.example.com/`
- 登录页面正常展示。
- 使用种子账号登录。

种子账号仅用于首次验证：

| 用户 | 密码 | 角色 |
|---|---|---|
| admin | Admin@123456 | ADMIN |
| demo | Demo@123456 | USER |

上线后必须创建新管理员或修改默认密码，不要长期保留默认密码。

### 13.2 业务验收

- 登录 admin。
- 创建或查看知识库。
- 上传一个小 PDF/DOCX/TXT。
- 确认文档状态变为 READY。
- 发起一次问答。
- 确认 SSE 流式输出正常。
- 确认回答能引用知识库内容。

### 13.3 资源验收

```bash
docker stats
free -h
df -h
```

验收标准：

- 空闲状态下系统仍有可用内存。
- 上传小文档时没有 OOM。
- MySQL、Qdrant、Backend 没有频繁重启。
- 已有项目访问正常。

## 14. 日常运维命令

### 14.1 查看服务

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
docker stats
```

### 14.2 查看日志

```bash
docker logs -f --tail=200 aap-backend
docker logs -f --tail=200 aap-frontend
docker logs -f --tail=200 aap-mysql
docker logs -f --tail=200 aap-qdrant
```

### 14.3 重启服务

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod restart backend
docker compose -f docker-compose.prod.yml --env-file .env.prod restart frontend
```

### 14.4 停止服务

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod down
```

注意：不要加 `-v`，否则会删除数据卷。

## 15. 备份与恢复

### 15.1 备份 MySQL

```bash
mkdir -p /opt/aap/backups/mysql

export MYSQL_ROOT_PASSWORD='你的MySQL root密码'
export MYSQL_DATABASE='ai_assistant'

docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T mysql \
  mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" \
  > /opt/aap/backups/mysql/aap_$(date +%F_%H%M%S).sql
```

### 15.2 备份 Docker volumes

```bash
mkdir -p /opt/aap/backups/volumes

docker run --rm \
  -v aap_qdrant_data:/data:ro \
  -v /opt/aap/backups/volumes:/backup \
  alpine tar czf /backup/aap_qdrant_data_$(date +%F_%H%M%S).tar.gz -C /data .

docker run --rm \
  -v aap_backend_files:/data:ro \
  -v /opt/aap/backups/volumes:/backup \
  alpine tar czf /backup/aap_backend_files_$(date +%F_%H%M%S).tar.gz -C /data .
```

### 15.3 恢复 MySQL

恢复前先停后端：

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod stop backend
```

```bash
export MYSQL_ROOT_PASSWORD='你的MySQL root密码'
export MYSQL_DATABASE='ai_assistant'

docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T mysql \
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" \
  < /opt/aap/backups/mysql/你的备份文件.sql
```

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod start backend
```

### 15.4 定时备份（建议）

每天凌晨备份 MySQL（按需改密码与路径）：

```bash
crontab -e
```

示例：

```cron
15 3 * * * export MYSQL_ROOT_PASSWORD='你的密码' MYSQL_DATABASE='ai_assistant'; cd /opt/aap/ai-assistant-platform && docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T mysql mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" > /opt/aap/backups/mysql/aap_$(date +\%F).sql
```

定期清理旧备份与无用 Docker 镜像，避免磁盘涨满：

```bash
docker system df
df -h
```

## 16. 升级流程

每次升级前**必须**先按第 15 节备份 MySQL 和关键 volume，并记下当前 commit：

```bash
cd /opt/aap/ai-assistant-platform
git rev-parse --short HEAD > /opt/aap/backups/last_good_commit.txt
# 执行 15.1 / 15.2 备份
git pull
```

2C4G：在构建机重新 `build` + `save`，上传后 `docker load`，再：

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/seed_menus.py
curl -i http://127.0.0.1:18000/ready
```

内存充足时可在服务器 `build` 后同样 `up -d`。

升级后验证：前端可开、登录正常、`/ready` 正常、知识库与问答正常。

若 Alembic 迁移失败：不要继续放量；用第 15.3 节恢复库，再按第 17 节回滚代码/镜像。

## 17. 回滚流程

```bash
cd /opt/aap/ai-assistant-platform
git log --oneline -5
git checkout "$(cat /opt/aap/backups/last_good_commit.txt)"
# 2C4G：重新 load 上一版镜像；或重新 build 该 commit
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

若升级已执行数据库迁移：

- 代码回滚**不会**自动回滚 schema。
- 用升级前的 MySQL 备份按 15.3 恢复，再启动后端。

注意：

- 数据卷不会因普通 `up -d` / `down` 被删除。
- 不要执行 `docker compose down -v`，除非明确要清空所有数据。

## 18. 常见问题

### 18.1 前端打开后请求 mock 地址

原因：构建未使用 `Dockerfile.prod`，或本地改过 `.env.production` 仍指向 mock。

处理：确认用 `frontend/scripts/deploy/Dockerfile.prod` 构建，或保证：

```env
VITE_GLOB_API_URL=/api/v1
```

然后重建前端：

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod build frontend
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d frontend
```

### 18.2 `/ready` 返回 MySQL fail

```bash
docker logs --tail=200 aap-mysql
docker logs --tail=200 aap-backend
```

检查：`MYSQL_HOST=mysql`、密码一致、MySQL 已 healthy、已执行 Alembic。

### 18.3 `/ready` 返回 Qdrant fail

```bash
docker logs --tail=200 aap-qdrant
docker logs --tail=200 aap-backend
```

检查：`QDRANT_URL=http://qdrant:6333`、容器健康、服务器内存是否不足。

### 18.4 上传文档失败

检查：Nginx `client_max_body_size`、`.env.prod` 的 `MAX_UPLOAD_SIZE_MB`、`aap_backend_files` volume、后端解析日志。

### 18.5 SSE 问答不流式输出

确认宿主机 Nginx `/api/v1/` 含：

```nginx
proxy_buffering off;
proxy_cache off;
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
```

### 18.6 服务器内存不足

1. 停止任何 `docker build`。
2. `docker stats` / `free -h`。
3. 降低并发导入。
4. 保持 backend `--workers 1`。
5. 改用第 12 节本地构建。
6. 长期：升到 4 核 8G 或拆分 MySQL/Qdrant。

### 18.7 本机构建时 apt / npm / pip 在 Docker 内超时

现象：宿主机浏览器/PowerShell 能上网，但 `docker build` 里访问 `deb.debian.org`、`registry.npmjs.org`、`pypi` 全部超时。

原因：Docker Desktop 容器网络出站异常（与镜像源无关）。

推荐做法（本机有 Node + Python 时）：

```powershell
# 在仓库根目录
.\scripts\build-prod-images.ps1
```

脚本会：本机 `pnpm build:ele` → 本机下载 Linux 版 pip wheels → 离线打前端/后端镜像。

完成后：

```powershell
docker images aap-frontend:prod
docker images aap-backend:prod
docker save aap-frontend:prod aap-backend:prod -o aap-images.tar
```

也可尝试在 Docker Desktop → Settings → Network 中改 DNS（如 `8.8.8.8` / `114.114.114.114`）后重试普通 `compose build`。

### 18.8 问答时模型 API 调用失败

`/ready` 只检查 MySQL 和 Qdrant。上线前在服务器验证外网模型可达：

```bash
curl -I https://api.openai.com/v1
```

若用阿里云或其他 OpenAI Compatible 网关，换成 `.env.prod` 里的 `LLM_BASE_URL` / `EMBEDDING_BASE_URL`。

## 19. 最终上线检查表

- [ ] 域名已解析到服务器；安全组已放行 80/443。
- [ ] 宿主机 Nginx 已安装；原有项目访问正常。
- [ ] Docker 和 Docker Compose 已安装；建议已配置 swap。
- [ ] 已确认仓库内生产文件存在（Compose / Dockerfile / `.env.prod.example`）。
- [ ] `.env.prod` 已配置真实密钥、数据库密码、API Key、CORS 域名。
- [ ] 服务器已验证 LLM/Embedding API 可访问（真实上线时）。
- [ ] 2C4G：已用第 12 节导入前端/后端镜像（或内存充足时服务器 build 成功）。
- [ ] `docker compose config` 通过；所有容器 healthy。
- [ ] `alembic upgrade head` 已执行。
- [ ] `seed_v1.sql` 已导入；`seed_menus.py` 已执行。
- [ ] `/health`、`/ready`、HTTPS、登录、上传、问答正常。
- [ ] 默认 admin/demo 密码已处理。
- [ ] 已完成至少一次 MySQL 备份；建议已加 crontab。
- [ ] 已记录回滚 commit（`/opt/aap/backups/last_good_commit.txt`）。

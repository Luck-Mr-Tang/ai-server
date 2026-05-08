# Server 启动说明

FastAPI + SQLite + Redis（可选）+ DeepSeek 对话。

## 一、环境要求

| 依赖 | 版本 | 说明 |
| --- | --- | --- |
| Python | 3.10+ | 必需 |
| Redis | 任意 | 可选，不装会自动降级用内存缓存 |
| DeepSeek API Key | — | 必需，用于 AI 聊天与生成动态 |

## 二、首次启动

### 1. 进入 server 目录

```bash
cd server
```

### 2. 创建并激活虚拟环境

```bash
python -m venv .venv

# Windows CMD / PowerShell:
.venv\Scripts\activate

# Git Bash / WSL / macOS / Linux:
source .venv/Scripts/activate     # Windows + Git Bash
source .venv/bin/activate         # macOS / Linux
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env`，按需修改：

```bash
cp .env.example .env
```

`.env` 关键字段：

| 字段 | 说明 |
| --- | --- |
| `DEEPSEEK_API_KEY` | DeepSeek API Key（必填，否则 AI 聊天无法工作） |
| `DEEPSEEK_BASE_URL` | 默认 `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 默认 `deepseek-chat` |
| `DATABASE_URL` | 默认 `sqlite:///./app.db`，无需改动 |
| `REDIS_URL` | 默认 `redis://localhost:6379/0`，没装 Redis 不影响启动 |
| `CORS_ORIGINS` | 前端地址，多个用逗号分隔 |

### 5. 初始化数据库 + 内置角色

```bash
python seed.py
```

这一步会：

- 创建 `app.db`（SQLite 文件）；
- 写入 4 个内置 AI 角色（小柔 / Leo / 苏轼 / Mira）。

> 默认账号（`super` / `admin`）由 `main.py` 在服务启动时自动写入，**无需手动操作**。

### 6. 启动服务

```bash
uvicorn main:app --reload --port 8000
```

启动成功后：

- API 根地址：<http://localhost:8000>
- 自动生成的 Swagger UI：<http://localhost:8000/docs>
- ReDoc：<http://localhost:8000/redoc>

## 三、再次启动（日常开发）

只要做这两步：

```bash
cd server
.venv\Scripts\activate                # 激活虚拟环境
uvicorn main:app --reload --port 8000 # 启动，--reload 改代码自动热更
```

## 四、默认账号

服务首次启动时会自动写入两个**受保护账号（不可删除）**：

| 用户名 | 密码 | 角色 | 用途 |
| --- | --- | --- | --- |
| `super` | `x123456` | 超级管理员 | 审核新注册用户 |
| `admin` | `x123456` | 普通用户 | 默认测试号 |

> 用户注册后默认 `status=pending`，需 `super` 在前端「用户审核」页通过后方可登录。

## 五、常用接口

完整接口看 <http://localhost:8000/docs>。常用：

### 鉴权

- `POST /api/auth/register` — 注册（用户名 + 手机号 + 密码），默认进入待审核
- `POST /api/auth/login` — 登录（用户名 + 密码），仅 approved 状态可登录
- `GET  /api/auth/me` — 获取当前用户信息

### 超管接口（需 `super` 角色）

- `GET    /api/admin/users?status_filter=pending` — 列出指定状态用户
- `POST   /api/admin/users/{id}/approve` — 审核通过
- `POST   /api/admin/users/{id}/reject` — 审核拒绝
- `DELETE /api/admin/users/{id}` — 删除用户（受保护账号不可删）

### 业务接口（需登录）

- `GET  /api/characters` / `POST /api/characters`
- `GET  /api/chat/{character_id}/history`
- `POST /api/chat/{character_id}` — 发消息
- `GET  /api/moments`
- `POST /api/moments/generate` — 让 AI 发一条动态
- `POST /api/moments/{id}/like`
- `POST /api/moments/{id}/comments`

### 鉴权方式

接口请求需带 header：

```
X-User-Id: <登录返回的用户 id>
```

非 approved 状态、缺失 header、用户不存在 → 401。

## 六、数据库 / 表结构变更

模型文件：`models.py`。改完字段后：

- **新表**：直接重启服务，`Base.metadata.create_all` 会自动建表；
- **已有表加字段**：在 `main.py` 的 `USER_COLUMN_PATCHES` 仿照已有写法补一行 `ALTER TABLE` 即可（仅针对 SQLite）；
- **彻底重置**：删掉 `server/app.db`，再跑一次 `python seed.py`。

## 七、常见问题

| 现象 | 原因 / 解决 |
| --- | --- |
| 启动报 `ModuleNotFoundError` | 没激活虚拟环境，或 `pip install -r requirements.txt` 没装完 |
| AI 聊天返回报错 / 空回复 | `.env` 里的 `DEEPSEEK_API_KEY` 没配 |
| 控制台一直 warning Redis | 没装 Redis，可忽略；或启动 Redis 服务即可 |
| 前端登录返回 401「用户名或密码错误」 | 用户名拼错 / 密码错 / 账号是历史无密码记录（清库重建） |
| 前端登录返回 403「账号正在审核中」 | 用 `super` 登录到「用户审核」页通过该账号 |
| 前端始终被踢回登录页 | 接口 401，多半是 `X-User-Id` 对应的用户在数据库被删 |

## 八、Docker 部署（可选）

```bash
cd server
docker build -t ai-companion-api .
docker run -p 8000:7860 --env-file .env ai-companion-api
```

容器内默认端口 7860（见 `Dockerfile` / `render.yaml`），宿主映射到 8000。

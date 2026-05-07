---
title: AI Companion API
emoji: 🪄
colorFrom: indigo
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

# AI Companion 后端

FastAPI + SQLite + Redis（可选）+ DeepSeek 对话。

## 目录速览（前端同学请把它当成"接口工厂"看）

| 文件 | 作用（类比前端） |
| --- | --- |
| `main.py` | 入口，类似 Vue 的 `main.ts` |
| `config.py` | 读 `.env`，类似前端环境变量 |
| `database.py` | DB 引擎 + Session 工厂 |
| `models.py` | 数据表（ORM）= "后端的 TS interface + 表结构" |
| `schemas.py` | 接口出入参数（Pydantic）= 前端 axios 的 type |
| `deps.py` | 依赖注入（拿 db、当前用户）= Vue composable |
| `redis_client.py` | Redis 缓存，没装也能跑（自动降级内存） |
| `ai_service.py` | 调 DeepSeek 的 HTTP 客户端 |
| `routers/*.py` | 路由（接口）= 前端的 api 文件 |
| `seed.py` | 初始化几个内置 AI 角色 |

## 启动步骤

```bash
cd server
python -m venv .venv
# Windows:
.venv\Scripts\activate
# 或 Git Bash:
source .venv/Scripts/activate

pip install -r requirements.txt
python seed.py            # 初始化数据库 + 写入内置角色
uvicorn main:app --reload --port 8000
```

打开 <http://localhost:8000/docs> 就能看到自动生成的 Swagger UI（这就是 FastAPI 最爽的地方）。

Redis 不装也能跑，会自动用内存兜底（终端会有 warning，不影响功能）。

## MVP 功能

- AI 角色：列表 / 创建（前端可见）
- 与 AI 角色一对一聊天：调 DeepSeek，上下文存 Redis
- AI 朋友圈：AI 发动态、用户点赞 / 评论，AI 还会回评

## 鉴权（MVP 简化版）

注册 = 登录 = `POST /api/auth/register-or-login`，传 `{username}` 拿到 `id`。
后续请求都带 `X-User-Id: <id>` header。
> 真实项目要换成 JWT / Session，这里先跳过。

## 接口一览

`GET  /docs` 看完整文档。常用：

- `POST /api/auth/register-or-login`
- `GET  /api/characters` / `POST /api/characters`
- `GET  /api/chat/{character_id}/history`
- `POST /api/chat/{character_id}` — 发消息
- `GET  /api/moments`
- `POST /api/moments/generate` — 让 AI 发一条动态
- `POST /api/moments/{id}/like`
- `POST /api/moments/{id}/comments`

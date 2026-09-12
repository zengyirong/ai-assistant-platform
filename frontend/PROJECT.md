# 本仓库中的前端

本目录为精简后的 [vue-vben-admin](https://github.com/vbenjs/vue-vben-admin)（Vben Admin 5）骨架。

一期**仅保留** Element Plus 应用：

```text
apps/web-ele          # 主应用
apps/backend-mock     # 开发期 mock（登录等）
packages/ / internal/ # 框架公共包（勿删）
```

已移除：`web-antd` / `web-naive` / `web-tdesign` / `playground` / `docs`，以及 web-ele 内演示页（Demos、Analytics、Workspace、About、Vben 推广菜单）。

当前菜单仅：

```text
概览 → 首页（空白壳）
```

后续业务按 Phase 0 约定扩展：

```text
apps/web-ele/src/
  api/          → auth / knowledge / document / conversation
  views/        → knowledge / document / ai-chat / system
  components/ai → Chat / Citation / Streaming
  composables/  → useSseChat / useAbortChat / useCitation
  stores/       → conversation / knowledge
  types/        → knowledge / document / conversation / sse
```

## 启动

```bash
# 终端 1：后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端 2：前端（已对接真实后端，不再走 Nitro mock）
cd frontend
pnpm install
pnpm run dev:ele
```

默认登录（真实后端种子）：`admin` / `Admin@123456`

前端请求：`/api/*` → Vite 代理 → `http://127.0.0.1:8000/api/v1/*`

> 改 `.env.development` 后需重启 `pnpm run dev:ele`；若仍看到旧登录态，请清空浏览器 LocalStorage。

## 说明

- Chat / Citation 等 AI 组件按 Phase 0 自研，不强行塞进 Vben CRUD 模板。
- 已去掉百度统计与演示通知假数据。

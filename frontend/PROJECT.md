# 本仓库中的前端

本目录为 [vue-vben-admin](https://github.com/vbenjs/vue-vben-admin)（Vben Admin 5）官方 monorepo 骨架。

一期主应用使用 **Element Plus** 版本：

```text
apps/web-ele
```

与 Phase 0 目录约定对应关系：

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
cd frontend
pnpm install
pnpm run dev:ele
# 或查看 package.json scripts
```

后端默认：`http://127.0.0.1:8000`（需在 web-ele 环境变量中配置 API 地址）。

## 说明

- `create-vben` CLI 当前环境不可用，改为直接纳入官方仓库源码。
- 已移除嵌套 `.git`，随本 monorepo 一并版本管理。
- Chat / Citation 等 AI 组件按 Phase 0 自研，不强行塞进 Vben CRUD 模板。

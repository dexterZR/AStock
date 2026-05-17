# A 股行情分析平台

Vue 3 + TypeScript 前端 + Python FastAPI 后端。

## 技术栈

**前端**：Vue 3 / TypeScript / Vite / Element Plus / ECharts / lightweight-charts
**后端**：Python / FastAPI / tushare / Docker

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev      # 开发
npm run build    # 构建
npm run preview  # 预览
```

### 后端

```bash
cd backend
python -m uvicorn main:app --reload
```

### Docker 部署

```bash
docker-compose up --build
```

## Agent 工作流

详见 `docs/agent-rules.md`。

### 角色分工

| Agent | 职责 |
|-------|------|
| Hermes | 中枢，判断/调度/整合 |
| OpenClaw | 纯展示层前端 |
| Claude Code 前端 | 复杂前端 |
| Claude Code 后端 | 后端 + 数据 |

## 目录结构

```
stock-analyzer/
├── frontend/         # Vue 3 前端
├── backend/          # Python FastAPI 后端
├── docs/             # 文档
│   ├── agent-rules.md   # Agent 分工规则
│   └── superpowers/     # 规划文档
└── docker-compose.yml
```
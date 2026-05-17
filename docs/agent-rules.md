# Agent 工作流规则

## 角色分工

| Agent | 职责范围 | 工作目录 |
|-------|---------|---------|
| **Hermes** | 中枢，判断/调度/整合/回复，所有分析任务 | ~ |
| **OpenClaw** | 纯展示层前端（HTML/CSS/Vue template） | `~/Desktop/stock-analyzer/frontend/` |
| **Claude Code（前端）** | 复杂前端，有逻辑的组件、状态管理、API 调用 | `~/Desktop/stock-analyzer/frontend/` |
| **Claude Code（后端）** | 后端、数据库、tushare 数据拉取、API | `~/Desktop/stock-analyzer/backend/` |

## 任务分流规则

### Hermes 判断维度
1. 任务类型：分析/调度 vs 编码
2. 编码任务：前端 vs 后端
3. 前端复杂度：纯展示 vs 有逻辑

### 分流逻辑（伪代码）

```
if "非编码任务":
    → Hermes 自行处理
elif "后端任务":
    → Claude Code（后端）
elif "前端任务" and "有状态/逻辑/API":
    → Claude Code（前端）
elif "前端任务" and "纯展示/样式/静态组件":
    → OpenClaw
else:
    → Claude Code（前端）
```

### 关键词参考

| 关键词 | 指向 |
|--------|------|
| 改颜色、加图标、样式、布局 | OpenClaw |
| 修 bug、重构、组件、多文件 | Claude Code 前端 |
| API、数据拉取、数据库、FastAPI | Claude Code 后端 |
| 分析、总结、调度、飞书 | Hermes |

## 协作规范

### OpenClaw 规则
- 只碰 `frontend/src/` 中的展示层（template、CSS）
- 不碰 `store/`、`composables/`、`api/` 目录
- 改动后运行 `npm run build` 验证

### Claude Code（前端）规则
- 碰前端全目录，包括状态管理和业务逻辑
- 完成后输出：改了哪些文件、怎么验证

### Claude Code（后端）规则
- 碰 `backend/` 全目录
- 不碰 `frontend/` 除非明确说跨栈联动
- 完成后输出：改了哪些文件、API 变化说明

### 文件冲突处理
两个 Agent 尽量不碰同一个文件。
如需同时改同一文件，按顺序执行，禁止并发。

## 共享知识库

所有 Agent 开工前应读：
- `docs/agent-rules.md`（本文件）
- `docs/architecture.md`（技术架构）
- `README.md`（项目说明）

## 验证标准

| 任务类型 | 验证方式 |
|---------|---------|
| 前端展示改动 | `npm run build` 无报错 |
| 前端逻辑改动 | `npm run build` + 功能测试 |
| 后端改动 | `python -m pytest` 或接口测试 |
| 数据任务 | 拉取数据核对字段 |

## 禁止事项

- 禁止 Agent 之间直接互调（通过 MCP 任务委派收益不大）
- 禁止不验证就汇报完成
- 禁止跨 Agent 同时改同一文件
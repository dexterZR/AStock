# A 股行情分析平台

A股全市场行情分析、技术指标计算、智能选股筛选系统。支持实盘行情、AI 驱动选股对话、多维度股票分析、投资组合管理。

## 功能特性

- **行情总览** — 大盘涨跌分布、板块热度、资金流向
- **智能选股** — AI 对话驱动选股，支持 80+ 条件组合筛选（技术面/基本面/形态）
- **多 Agent 分析** — 技术面/基本面/催化剂三维深度分析 + 综合评分
- **K 线图表** — 日/周/月级别 K 线，支持 MA/MACD/RSI/KDJ/布林带指标
- **投资组合** — 持仓管理、交易记录、风险预警
- **行业轮动** — 行业排名、成分股涨跌分布
- **消息面** — 市场新闻、个股舆情追踪
- **定时同步** — 自动交易日数据同步、指标计算、信号扫描

## 技术栈

| 层 | 技术 |
|---|------|
| **前端** | Vue 3 + TypeScript + Vite + Element Plus + ECharts + lightweight-charts |
| **后端** | Python 3.11+ / FastAPI / Motor (MongoDB async) |
| **数据库** | MongoDB (主存储) + Redis (缓存/限流/SSE) |
| **数据源** | Tushare Pro / AKShare |
| **AI** | OpenAI 兼容 LLM API |
| **部署** | Docker / Docker Compose |

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.11+
- MongoDB 6+
- Redis 6+

### 1. 配置

```bash
# 后端配置
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 Tushare Token 等配置
```

### 2. 运行后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 3. 运行前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### Docker 部署

```bash
docker-compose up --build
```

## 项目结构

```
stock-analyzer/
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # API 请求层
│   │   ├── components/     # 组件
│   │   ├── composables/    # 组合式函数
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── types/          # TypeScript 类型定义
│   │   └── views/          # 页面
│   └── vite.config.ts
├── backend/                # Python FastAPI 后端
│   ├── app/
│   │   ├── api/            # 路由 + 中间件
│   │   ├── core/           # 配置 / 数据库连接
│   │   ├── infrastructure/ # Redis / SSE / 数据源
│   │   ├── jobs/           # 定时任务
│   │   ├── models/         # Pydantic 模型
│   │   ├── repos/          # 数据访问层
│   │   └── services/       # 业务逻辑
│   └── tests/
└── docker-compose.yml
```

## 配置说明

| 环境变量 | 说明 | 必需 |
|---------|------|------|
| `MONGO_URI` | MongoDB 连接地址 | 是 |
| `REDIS_URL` | Redis 连接地址 | 是 |
| `TUSHARE_TOKEN` | Tushare Pro Token（用于日K线同步） | 推荐 |
| `LLM_API_KEY` | LLM API Key（AI 选股对话） | 可选 |
| `JWT_SECRET` | JWT 签名密钥 **（生产环境必须修改！）** | 是 |
## License

MIT

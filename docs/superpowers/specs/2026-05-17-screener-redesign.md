# 选股器全面重构设计文档

## 概述

对现有选股器进行全面重构，从 4 个基础筛选维度扩展为覆盖技术信号、基本面、形态识别、资金流向的全方位选股系统，并深度集成 AI 能力（自然语言选股、AI 智能筛选、AI 解读结果、AI 每日推荐），结果支持多视图+可视化展示。

## 架构方案：混合方案（预计算信号 + 实时聚合）

技术信号和形态标签预计算存储，基本面/资金流向/简单数值范围用 MongoDB aggregation 实时查询。兼顾性能和灵活性。

## 三大模块

### 1. 条件引擎（Condition Engine）

将用户筛选意图翻译为数据库查询。

#### 筛选维度

| 类别 | 条件项 | 数据来源 | 查询方式 |
|------|--------|----------|----------|
| 技术信号 | MA金叉/死叉、MACD金叉、KDJ金叉、RSI超买超卖、布林突破、均线多头/空头排列 | `screener_signals` 预计算 | `$match` 布尔字段 |
| 形态识别 | 突破N日新高、N日内涨幅超X%、连续N日放量、V型反转、缩量盘整 | `screener_signals` 预计算 | `$match` 布尔/枚举字段 |
| 基本面 | PE/PB/ROE/营收增长率/净利润增长率/股息率/市值 | `fundamentals` 集合 | 实时聚合范围查询 |
| 资金流向 | 主力净买入、大单净买入、北向资金持仓变动、行业资金流入 | `capital_flow` 集合 | 实时聚合范围查询 |
| 行情 | 价格区间、涨跌幅、换手率、成交量 | `daily_quotes` 集合 | 实时聚合范围查询 |

#### 条件标签卡片交互

- 点击「+ 添加条件」弹出分类选择面板（技术/基本/形态/资金/行情）
- 选择具体条件后弹出参数设置（如 MA5 上穿 MA20、PE 范围 0~30）
- 确认后生成彩色标签卡片，按类别分色
- 所有条件默认 AND 关系；支持「条件组」，组内可设 OR
- 每个标签右侧有 × 可删除

#### 策略模板（6 个预设）

1. **突破新高** — 突破20日新高 + 放量 + MA多头
2. **均线多头** — MA5>MA10>MA20>MA60 + MACD金叉
3. **超跌反弹** — RSI6<30 + 股价<布林下轨 + 缩量
4. **低估值** — PE<20 + ROE>15% + 股息率>3%
5. **放量上攻** — 换手率>5% + 涨幅>3% + 主力净买入
6. **北向加仓** — 北向资金增持 + PE<30 + 均线多头

点击模板自动填充条件标签卡片，用户可修改后执行。

### 2. AI 中枢（AI Hub）

四个 AI 能力深度参与选股全流程。

#### 自然语言选股

- 用户输入自然语言描述（如"找近期放量突破的低价股"）
- 后端调用 LLM，将自然语言解析为结构化条件列表
- 前端自动填充条件标签卡片，用户可修改后执行
- API: `POST /api/screener/ai-parse`，请求体 `{ query: string }`，返回 `{ conditions: Condition[] }`

#### AI 智能筛选

- 用户提模糊条件（如"帮我找值得关注的科技股"）
- AI 结合当日市场数据、热点、资金流向，智能生成筛选结果
- 每只股票附带 AI 选择理由
- API: `POST /api/screener/ai-pick`，请求体 `{ query: string }`，返回 `{ stocks: StockWithReason[] }`

#### AI 解读结果

- 对筛选结果批量分析，输出：
  - 整体市场画像（行业分布、估值水平、资金特征）
  - 个股点评（技术面/基本面/催化剂三维评分）
  - 风险提示和操作建议
- API: `POST /api/screener/ai-analyze`，请求体 `{ ts_codes: string[] }`，返回 `{ overview: string, stocks: AnalysisResult[] }`

#### AI 每日推荐

- 每日定时任务，AI 分析市场热点 + 资金流向
- 生成 2-3 个推荐策略方向 + 对应选股结果
- 展示在选股器页面的"今日AI推荐"区域
- API: `GET /api/screener/ai-daily`，返回 `{ recommendations: DailyRecommendation[] }`
- 定时任务：每日 9:30 执行，存入 `ai_daily_recommendations` 集合

### 3. 结果展示（Result View）

#### 四种视图

1. **表格视图**（默认）— 增强版数据表格
   - 列：代码、名称、行业、现价、涨跌幅、PE、RSI、信号标签、操作
   - 支持排序、多选、分页

2. **卡片视图** — 迷你K线 + 关键指标
   - 每张卡片：迷你K线图 + 名称/代码 + 3-4个核心指标 + 信号标签
   - 网格布局，直观浏览

3. **气泡图** — 市值 vs 涨跌幅
   - X轴涨跌幅、Y轴市值、气泡大小=成交量、颜色=行业
   - 鼠标悬停显示详情

4. **热力图** — 行业分布
   - 按行业聚合，色块大小=股票数量，颜色=平均涨跌幅
   - 点击行业展开个股

#### 底部操作栏

- AI解读结果 / 对比 / 导出CSV

## 数据层

### 新增集合

#### `screener_signals`

预计算的技术信号和形态标签，每日由定时任务更新。

```python
{
    "ts_code": "600519.SH",
    "trade_date": "2026-05-16",
    # 技术信号（布尔）
    "ma5_cross_ma10": True,      # MA5 上穿 MA10
    "ma5_cross_ma20": False,
    "ma10_cross_ma20": True,
    "macd_cross": True,          # MACD 金叉
    "kdj_cross": True,           # KDJ 金叉
    "rsi_oversold": False,       # RSI6 < 30
    "rsi_overbought": False,     # RSI6 > 70
    "boll_breakout_up": True,    # 突破布林上轨
    "boll_breakout_down": False, # 跌破布林下轨
    "ma_bullish": True,          # 均线多头排列
    "ma_bearish": False,         # 均线空头排列
    "volume_surge": True,        # 放量（量比>2）
    "volume_shrink": False,      # 缩量（量比<0.5）
    # 形态信号
    "breakout_20d_high": True,   # 突破20日新高
    "breakout_60d_high": False,
    "drop_20d_low": False,
    "v_shape_recovery": False,   # V型反转
    "consolidation": False,      # 缩量盘整
    "continuous_up_3d": True,    # 连续3日上涨
    "continuous_volume_3d": False, # 连续3日放量
}
```

#### `fundamentals`

基本面数据，每日同步。

```python
{
    "ts_code": "600519.SH",
    "trade_date": "2026-05-16",
    "pe": 28.5,
    "pb": 8.2,
    "roe": 30.5,
    "revenue_growth": 0.15,       # 营收增长率
    "profit_growth": 0.18,        # 净利润增长率
    "dividend_yield": 0.025,      # 股息率
    "total_mv": 2100000000000,    # 总市值
    "circ_mv": 1800000000000,     # 流通市值
}
```

#### `capital_flow`

资金流向数据，每日同步。

```python
{
    "ts_code": "600519.SH",
    "trade_date": "2026-05-16",
    "main_net_buy": 50000000,     # 主力净买入
    "big_net_buy": 30000000,      # 大单净买入
    "north_holding_change": 0.02, # 北向资金持仓变动比例
    "sector_flow": {              # 行业资金流入
        "industry": "白酒",
        "net_amount": 200000000,
    }
}
```

#### `ai_daily_recommendations`

AI 每日推荐结果。

```python
{
    "date": "2026-05-16",
    "recommendations": [
        {
            "title": "科技板块资金持续流入",
            "strategy": "关注半导体和AI相关标的",
            "conditions": [...],  # 对应筛选条件
            "stocks": [...],      # 推荐股票列表
            "reason": "...",
        }
    ]
}
```

### 数据同步定时任务

1. **`compute_screener_signals`** — 每日计算技术信号和形态标签，写入 `screener_signals`
2. **`sync_fundamentals`** — 每日从 tushare/akshare 同步基本面数据，写入 `fundamentals`
3. **`sync_capital_flow`** — 每日从 akshare 同步资金流向数据，写入 `capital_flow`
4. **`generate_ai_daily`** — 每日 9:30 生成 AI 推荐策略

## API 设计

### 筛选 API

```
POST /api/screener
Body: {
    "conditions": [
        { "category": "technical", "field": "ma5_cross_ma20", "op": "eq", "value": true },
        { "category": "fundamental", "field": "pe", "op": "range", "min": 0, "max": 30 },
        { "category": "pattern", "field": "breakout_20d_high", "op": "eq", "value": true },
        { "category": "capital", "field": "main_net_buy", "op": "gt", "value": 0 },
        { "category": "quote", "field": "pct_change", "op": "range", "min": 0, "max": 10 }
    ],
    "limit": 50
}
```

### AI API

```
POST /api/screener/ai-parse    — 自然语言解析为条件
POST /api/screener/ai-pick     — AI 智能选股
POST /api/screener/ai-analyze  — AI 解读结果
GET  /api/screener/ai-daily    — AI 每日推荐
```

### 辅助 API

```
GET /api/screener/industries   — 行业列表
GET /api/screener/templates    — 策略模板列表
```

## 前端组件结构

```
views/Screener.vue                    — 选股器页面
├── components/screener/
│   ├── AIInput.vue                   — AI 自然语言输入框
│   ├── StrategyTemplates.vue         — 策略模板选择
│   ├── ConditionBuilder.vue          — 条件组合器
│   │   ├── ConditionTag.vue          — 单个条件标签卡片
│   │   ├── ConditionPicker.vue       — 条件选择弹窗
│   │   └── ConditionGroup.vue        — 条件组（OR 逻辑）
│   ├── ResultTable.vue               — 表格视图
│   ├── ResultCards.vue               — 卡片视图
│   ├── ResultBubble.vue              — 气泡图视图
│   ├── ResultHeatmap.vue             — 热力图视图
│   └── AIAnalysisPanel.vue           — AI 解读面板
├── stores/screenerStore.ts           — 状态管理（重构）
├── api/modules/screener.ts           — API 调用（重构）
└── types/screener.ts                 — 类型定义
```

## 设计风格

与现有 Anthropic 品牌风格完全统一：

- 配色：复用 `--claude-accent/blue/green` + `--color-up/down/warning` 体系
- 条件标签分色：技术=accent、基本=blue、形态=green、资金=warning、行情=text-secondary
- 排版：标题 Poppins 600-800、正文 Poppins 400-500、数字 JetBrains Mono
- 组件：沿用 el-card/button/table/input 覆盖样式
- 动画：fadeInUp 入场 + transition-fast/base 过渡
- AI 区域：accent 左边框 3px 标识，accent-light 背景
- 深色模式：通过 CSS 变量自动适配

## 后端文件变更

```
backend/app/
├── api/routers/screener.py           — 重构，支持新 API
├── services/screener_service.py      — 重构，条件引擎核心逻辑
├── services/screener_ai_service.py   — 新增，AI 中枢服务
├── models/screener.py                — 新增，筛选条件/结果模型
├── repos/screener_repo.py            — 新增，筛选数据访问层
├── repos/fundamental_repo.py         — 新增，基本面数据访问
├── repos/capital_flow_repo.py        — 新增，资金流向数据访问
├── jobs/compute_screener_signals.py  — 新增，预计算信号任务
├── jobs/sync_fundamentals.py         — 新增，基本面同步任务
├── jobs/sync_capital_flow.py         — 新增，资金流向同步任务
└── jobs/generate_ai_daily.py         — 新增，AI 每日推荐任务
```

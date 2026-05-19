# 自定义 LLM 配置功能设计

## 概述

在设置页面新增 LLM 配置功能，允许用户自定义 OpenAI 兼容的 LLM 提供商（如 DeepSeek、通义千问、Ollama 等），替换当前硬编码的 MiniMax 配置。选股器 AI 功能将使用用户配置的 LLM 工作。

## 方案选择

采用**方案 B：后端数据库存储 + 设置页面可编辑**。

理由：
- API Key 存数据库比存文件更安全、更易管理
- 前后端完整交互体验好
- 未来扩展为多配置方便（只需加列表）
- 符合项目已有的 MongoDB 架构

## 数据模型

在 MongoDB 中新增 `llm_config` 集合，单配置模式（只存一条文档）：

```python
{
    "_id": ObjectId,
    "name": "我的 DeepSeek",           # 配置名称/别名
    "base_url": "https://api.deepseek.com/v1",  # OpenAI 兼容 Base URL
    "api_key": "sk-xxx",              # API Key
    "model": "deepseek-chat",         # 模型名称
    "is_active": True,                # 是否启用
    "updated_at": "2026-05-19T10:00:00Z"
}
```

## 后端 API

新增 3 个端点，挂在 `/api/llm-config` 下：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/llm-config` | GET | 获取当前 LLM 配置（API Key 脱敏返回） |
| `/api/llm-config` | PUT | 保存/更新 LLM 配置 |
| `/api/llm-config/test` | POST | 测试连接 |

### GET /api/llm-config

返回当前配置，API Key 脱敏（只保留前3位和后4位，中间用 `••••` 替代）。如果数据库无配置，返回空数据。

### PUT /api/llm-config

接收完整配置并保存。检测到 API Key 为脱敏格式（`sk-••••`）时不覆盖数据库中原有的 Key，仅更新其他字段。使用 `upsert` 确保只有一条配置文档。

### POST /api/llm-config/test

用配置的 `base_url` + `api_key` + `model`，调用 OpenAI 兼容的 `chat.completions.create`，发送极简消息（`"Hi"`，`max_tokens=5`），超时 10 秒。返回：

```json
{
    "success": true/false,
    "message": "连接成功" / "认证失败：API Key 无效" / "连接超时" / ...
}
```

## screener_ai_service.py 改造

### 配置读取策略

`ScreenerAIService` 已持有 `self.db`，在 service 层方法中读取 LLM 配置后传给内部函数，避免将模块级函数改为异步。

新增模块级异步函数 `_get_llm_config(db)` 负责从数据库读取配置，回退到 `.env`：

```python
async def _get_llm_config(db) -> dict:
    config = await db["llm_config"].find_one({"is_active": True})
    if config and config.get("api_key"):
        return {
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "model": config["model"],
        }
    return {
        "api_key": settings.MINIMAX_API_KEY,
        "base_url": settings.MINIMAX_BASE_URL,
        "model": settings.MINIMAX_MODEL,
    }
```

### _get_llm_client()

改为接收配置字典参数，不再直接读取 settings：

```python
def _get_llm_client(config: dict):
    from openai import OpenAI
    return OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
    )
```

### _is_llm_available()

改为接收配置字典，检查 `api_key` 是否非空。

### 调用链调整

`ScreenerAIService` 的公开方法（`parse_natural_language`、`ai_pick`、`ai_chat`）在开头调用 `await _get_llm_config(self.db)` 获取配置，然后传入 `_call_llm` / `_call_chat_llm` 等内部函数。

## 前端改造

### Settings.vue

在现有系统设置 `el-card` 下方新增一个 `el-card`，**完全复用 Element Plus 组件和项目 CSS 变量**，保持风格统一：

- 使用 `el-card` + `el-form` + `el-form-item`，与系统设置卡片结构一致
- 使用项目 CSS 变量：`--claude-card`、`--claude-border`、`--claude-accent`、`--claude-text-secondary` 等
- API Key 输入框使用 `el-input` 的 `show-password` 属性，默认脱敏
- 连接状态指示器：`● 已连接`（绿色）或 `● 未配置`（灰色）
- 测试连接按钮点击后显示 loading，成功绿色提示，失败红色错误信息
- 保存配置时弹出确认对话框

表单字段：
1. 配置名称（`el-input`，placeholder："如：我的 DeepSeek"）
2. Base URL（`el-input`，placeholder："如：https://api.deepseek.com/v1"）
3. API Key（`el-input` + `show-password`，placeholder："输入 API Key"）
4. 模型名称（`el-input`，placeholder："如：deepseek-chat"）

### 前端 API 模块

新增 `frontend/src/api/modules/llmConfig.ts`：

```typescript
import request from '../request'

export const llmConfigApi = {
  getConfig: () => request.get('/llm-config'),
  saveConfig: (data: { name: string; base_url: string; api_key: string; model: string }) =>
    request.put('/llm-config', data),
  testConnection: () => request.post('/llm-config/test'),
}
```

### AIInput.vue 标识

在 AI 标签旁显示当前 LLM 配置名称（如 `AI · 我的 DeepSeek`），让用户知道当前用的是哪个 LLM。通过 store 或 API 获取配置名称。

## 错误处理与边界情况

| 场景 | 处理方式 |
|------|----------|
| 数据库无 LLM 配置 | 回退到 `.env` 中的 `MINIMAX_*` 配置，前端显示"未配置自定义 LLM，使用默认" |
| API Key 为空 | `_is_llm_available()` 返回 false，AI 功能降级为纯关键词匹配 |
| Base URL 不可达 | 测试连接返回错误提示，AI 调用失败时 catch 异常降级为关键词匹配 |
| 保存时 API Key 未修改（仍是脱敏值） | 后端检测到脱敏格式时保留数据库中原有的 Key 不覆盖 |
| 首次使用无任何配置 | 设置页面 LLM 卡片显示空表单，引导用户填写 |

## 安全考虑

- API Key 在 MongoDB 中明文存储（与当前 `.env` 明文存储一致，单用户场景足够）
- GET 接口返回脱敏 Key（只保留前3位和后4位）
- PUT 接口写入完整 Key，但检测到脱敏格式时不覆盖

## 涉及文件

### 新增文件
- `backend/app/api/routers/llm_config.py` — LLM 配置 API 路由
- `backend/app/models/llm_config.py` — LLM 配置数据模型
- `frontend/src/api/modules/llmConfig.ts` — 前端 API 模块

### 修改文件
- `backend/app/services/screener_ai_service.py` — 改造 LLM 客户端获取逻辑
- `frontend/src/views/Settings.vue` — 新增 LLM 配置卡片
- `frontend/src/components/screener/AIInput.vue` — 显示当前 LLM 名称
- `backend/app/api/__init__.py` 或主入口 — 注册新路由

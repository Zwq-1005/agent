# 医学统计 AI 助手 (Medical Statistics AI Assistant)

基于 AI + LangGraph 的智能医学统计分析平台。上传临床数据 → 数据清洗 → 自然语言描述需求 → 自动生成论文级统计结果。

## 功能特性

- **多格式数据导入**: 支持 CSV、Excel、JSON、SPSS (.sav)、Stata (.dta) 格式
- **智能字段识别**: 自动检测字段类型（数值/分类/等级/日期等）
- **数据质量报告**: 缺失值、异常值、重复行检测
- **数据清洗**: 缺失值填充、异常值剔除、重复行删除
- **医学统计模板库**: 预设 10+ 种常用医学统计 Prompt 模板
- **AI 自动分析**: LangGraph 编排 → Router → Coder → Executor → Reviewer 工作流
- **实时流式输出**: SSE 实时推送分析过程（思考 → 编码 → 执行 → 结果）
- **图表生成**: 自动生成箱线图、小提琴图、热力图、ROC曲线、森林图等
- **报告导出**: 一键下载 Word (docx) 或 PDF 格式统计分析报告

## 技术栈

### 后端
- **FastAPI** — Web 框架
- **SQLModel** — ORM (SQLite)
- **LangChain + LangGraph** — AI 工作流编排
- **pandas / scipy / numpy / statsmodels** — 统计分析
- **matplotlib / seaborn** — 数据可视化
- **python-docx / reportlab** — 报告生成
- **pyreadstat** — SPSS/Stata 文件读取

### 前端
- **Vue 3** + **TypeScript**
- **Naive UI** — 组件库
- **Pinia** — 状态管理
- **Vue Router** — 路由
- **Vite** — 构建工具

## 快速开始

### 环境变量

```bash
# 后端 (可选，设置了使用环境变量的值)
export OPENAI_API_KEY=your_api_key
export OPENAI_BASE_URL=https://api.openai.com/v1  # 或其他 OpenAI-compatible 接口
export LLM_MODEL=gpt-4o-mini
```

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动 (首次启动自动创建数据库和seed模板)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口，中间件，异常处理
│   ├── config.py            # 配置
│   ├── database.py          # 数据库 + seed数据
│   ├── models/              # 数据模型
│   │   ├── session.py       # 分析会话
│   │   ├── file.py          # 上传文件
│   │   ├── prompt.py        # Prompt模板
│   │   └── chat_message.py  # 聊天消息
│   ├── services/            # 业务逻辑
│   │   ├── file_service.py  # 文件解析、数据清洗、自动统计
│   │   └── report_service.py # Word/PDF 报告生成
│   ├── routers/             # API 路由
│   │   ├── upload.py        # 文件上传、字段定义、数据清洗
│   │   ├── session.py       # 会话管理、聊天消息
│   │   ├── analyze.py       # SSE 流式分析、报告导出
│   │   └── prompts.py       # Prompt 模板 CRUD
│   └── graph/               # LangGraph 工作流
│       ├── stats_graph.py   # 统计分析图 (Router → Coder → Executor → Reviewer)
│       └── sandbox.py       # 安全代码执行沙箱
├── requirements.txt
└── uploads/                 # 上传文件目录

frontend/
├── src/
│   ├── main.ts              # 入口
│   ├── App.vue              # 根组件
│   ├── router/              # 路由
│   ├── api/                 # API 层
│   │   ├── client.ts        # Axios 实例
│   │   └── analysis.ts      # 所有 API 函数
│   ├── stores/              # Pinia 状态
│   │   └── analysis.ts      # 分析状态
│   ├── components/          # 组件
│   │   ├── AppHeader.vue    # 导航栏
│   │   ├── ChatPanel.vue    # 对话面板
│   │   ├── DataPreviewTable.vue  # 数据预览表格
│   │   └── ResultPanel.vue  # 结果展示面板
│   ├── views/               # 页面
│   │   ├── HomePage.vue     # 首页
│   │   ├── DataImportPage.vue    # 数据导入 + 字段定义
│   │   ├── DataCleanPage.vue     # 数据清洗
│   │   ├── PromptTemplatesPage.vue # Prompt 模板
│   │   └── AnalysisWorkbench.vue   # 分析工作台
│   └── styles/              # 全局样式
└── vite.config.ts           # Vite 配置 (含代理)
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| **上传** | | |
| POST | `/api/v1/upload` | 上传数据文件 |
| GET | `/api/v1/upload/preview/{file_id}` | 获取文件预览 |
| PUT | `/api/v1/upload/{file_id}/fields` | 保存字段定义 |
| GET | `/api/v1/upload/{file_id}/fields` | 获取字段定义 |
| GET | `/api/v1/upload/{file_id}/quality` | 数据质量报告 |
| POST | `/api/v1/upload/clean` | 数据清洗 |
| GET | `/api/v1/upload/{file_id}/auto-stats` | 自动描述性统计 |
| **会话** | | |
| POST | `/api/v1/sessions` | 创建会话 |
| GET | `/api/v1/sessions` | 列出会话 |
| GET | `/api/v1/sessions/{id}` | 获取会话详情 |
| PUT | `/api/v1/sessions/{id}` | 更新会话 |
| DELETE | `/api/v1/sessions/{id}` | 删除会话 |
| POST | `/api/v1/sessions/{id}/messages` | 保存聊天消息 |
| GET | `/api/v1/sessions/{id}/messages` | 获取聊天记录 |
| **分析** | | |
| GET | `/api/v1/analyze/stream` | SSE 流式分析 |
| GET | `/api/v1/analyze/{id}/report` | 下载 Word/PDF 报告 |
| **模板** | | |
| GET | `/api/v1/prompts` | 列出模板 |
| GET | `/api/v1/prompts/categories` | 列出分类 |
| POST | `/api/v1/prompts` | 创建模板 |
| PUT | `/api/v1/prompts/{id}` | 更新模板 |
| DELETE | `/api/v1/prompts/{id}` | 删除模板 |

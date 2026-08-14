# Recall AI 智能错题本 · 全栈工程

面向学生的 AI 智能错题管理平台:拍照/截图/文本/对话录入 → AI 诊断 → SM-2 复习 → 变式训练 → 学习分析。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS + Pinia + Vue Router |
| 后端 | FastAPI + Uvicorn + SQLAlchemy 2.0 |
| 数据库 | SQLite(单文件,生产可换 PostgreSQL) |
| 向量库 | ChromaDB(错题去重 + RAG 检索) |
| 大模型 | DeepSeek API(诊断/讲解/变式/对话) |
| OCR | PaddleOCR-VL(HTTP 服务化调用,可降级) |
| PDF | ReportLab(错题报告导出) |

## 目录结构

```
recall-ai-app/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # pydantic-settings 配置
│   │   ├── database.py          # SQLAlchemy 引擎/会话
│   │   ├── models/              # user / question(SM-2状态/日志)
│   │   ├── schemas/             # Pydantic 请求/响应
│   │   ├── repositories/        # 数据访问层
│   │   ├── services/
│   │   │   ├── ai_service.py    # DeepSeek: 诊断/讲解/变式/对话
│   │   │   ├── vector_service.py# ChromaDB: 去重 + RAG
│   │   │   ├── ocr_service.py   # PaddleOCR-VL 封装
│   │   │   ├── review_service.py# SM-2 + 优先级调度
│   │   │   └── pdf_service.py   # ReportLab 导出
│   │   └── api/v1/              # questions / review / ai / analytics
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api/client.ts        # Axios 封装
    │   ├── stores/              # Pinia(错题/对话)
    │   ├── components/
    │   │   ├── ui/              # AppButton/AppCard/AppBadge/AppToast
    │   │   └── layout/TopNav.vue
    │   ├── views/               # Questions/AI/Analytics/Help
    │   ├── router/ types/
    │   ├── main.ts App.vue style.css
    ├── package.json vite.config.ts tailwind.config.js
    └── tsconfig.json
```

## 运行

### 后端

```bash
cd backend
cp .env.example .env          # 填入 DEEPSEEK_API_KEY
uv sync                        # 或 pip install -e .
uv run uvicorn app.main:app --reload --port 8000
# 文档: http://localhost:8000/docs
```

### 前端

```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173(Vite 代理 /api → 8000)
```

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/questions` | 录入错题(含 AI 诊断) |
| GET | `/api/v1/questions` | 错题列表(筛选/搜索/分页) |
| POST | `/api/v1/questions/{id}/confirm` | 确认/修正知识点 |
| DELETE | `/api/v1/questions/{id}` | 软删除 |
| GET | `/api/v1/questions/export/pdf` | 导出 PDF |
| GET | `/api/v1/reviews/today` | 今日复习清单 |
| POST | `/api/v1/reviews/{id}/submit` | 提交自评(SM-2 更新) |
| POST | `/api/v1/ai/chat` | AI 答疑对话 |
| POST | `/api/v1/ai/variant/generate` | 生成变式题 |
| GET | `/api/v1/analytics/weekly` | 周报 |

## 关键设计决策

1. **分层架构**:api → services → repositories → models,业务逻辑与 ORM 解耦
2. **AI 降级**:LLM/OCR/向量库任一不可用都不阻塞主流程(降级返回 + 人工修正兜底)
3. **向量去重**:题干向量化,相似度 > 0.95 自动合并(防重复录入)
4. **SM-2 独立服务**:纯函数算法,可单测;优先级权重(考试临近/错误频率/薄弱度/逾期)驱动每日清单
5. **色彩语义**:紫=AI、蓝=用户操作、绿=掌握、橙=模糊、红=错误(Tailwind token 固化)

## 产品文档(docs/)

| 文档 | 说明 |
|---|---|
| `docs/recall-ai-prd.md` | 产品需求文档(PRD)v1.0 |
| `docs/recall-ai-dev-plan.html` | 开发规划文档(8 章:总纲/里程碑/依赖树/API契约/规范/风险/验收/节奏) |
| `docs/recall-ai-business-flow-v2.html` | 业务流程设计 v2(核心闭环 + 三大流程 Mermaid) |
| `docs/recall-ai-competitor-analysis.html` | 竞品分析(蜜蜂试卷/作业帮/Anki) |
| `docs/recall-ai-ui-design-system.html` | UI/UX 设计系统(Notion × Glassmorphism) |
| `docs/recall-ai-web-ia.html` | Web 信息架构 |
| `docs/recall-ai-mvp-tech-doc.html` | MVP 技术文档 |
| `docs/recall-ai-wireframe.html` | 低保真线框图 |
| `docs/recall-ai-test-report.html` | 系统测试报告 |
| `docs/DESIGN.md` | 设计规范文档 |

## 快速启动

```bash
# 后端(需 Python 3.12+,首次安装依赖)
cd backend
pip install -r requirements.txt   # 或 poetry install
python -m uvicorn app.main:app --reload --port 8000

# 前端(需 Node 18+)
cd frontend
npm install
npm run dev   # http://localhost:5173
```

> 配置 DeepSeek API Key:启动后在前端「设置」页填写(运行版存后端内存)或写入 `backend/.env` 的 `DEEPSEEK_API_KEY`。

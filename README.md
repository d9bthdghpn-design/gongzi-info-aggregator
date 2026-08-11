# 对公资讯聚合系统

面向银行对公业务条线的公开资讯智能监测与商机挖掘平台。

## 🚀 快速部署

| 部署方式 | 难度 | 成本 | 推荐场景 |
|----------|------|------|----------|
| [Render 一键部署](DEPLOY.md) | ⭐ 简单 | 免费/7美元/月 | 快速体验、中小团队 |
| [Docker Compose](#一键启动) | ⭐⭐ 中等 | 服务器费用 | 自有服务器、生产环境 |
| 手动部署 | ⭐⭐⭐ 复杂 | 服务器费用 | 定制化需求 |

**👉 推荐新手用 Render 部署，10分钟搞定，免费试用！详细步骤看 [DEPLOY.md](DEPLOY.md)**

## 系统概述


本系统通过自动采集政府官网、招投标平台、园区网站等公开渠道的资讯信息，利用AI大模型进行智能分类打标、摘要生成和业务启示挖掘，帮助对公客户经理快速掌握区域内企业动态和业务机会，实现精准营销。

### 核心功能

- 🕷️ **多渠道自动采集** - 支持政府官网、招投标平台、园区网站等多渠道配置化采集
- 🤖 **AI智能处理** - 自动分类打标、摘要生成、业务启示挖掘、质量评分
- 📱 **移动端Web** - 响应式设计，手机端随时查看
- 🎯 **线索管理** - 商机线索上报、跟进、公海池流转
- 📰 **每日简报** - 按业务分类生成每日资讯简报
- 📋 **业务专题** - 聚焦重点领域，深度跟踪

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Vant UI |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| 数据库 | PostgreSQL 15 + Redis 7 |
| 采集 | Scrapy + 代理池 |
| AI | 大模型API + Celery异步任务 |
| 部署 | Docker Compose + Nginx |

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose v2+
- 至少 4GB 内存

### 一键启动

```bash
# 1. 克隆项目
cd gongzi-info-aggregator

# 2. 复制环境变量配置
cp .env.example .env
# 编辑 .env 文件，根据需要修改配置

# 3. 启动所有服务
docker-compose up -d

# 4. 查看启动状态
docker-compose ps
```

启动完成后：
- 前端访问地址：http://localhost:8080
- 后端API文档：http://localhost:8000/docs
- 默认账号：admin / admin123

### 停止服务

```bash
# 停止服务
docker-compose down

# 停止并删除数据（谨慎使用）
docker-compose down -v
```

## 项目结构

```
gongzi-info-aggregator/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/             # API路由层
│   │   ├── core/            # 核心模块（安全、异常等）
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic Schema
│   │   ├── services/        # 业务服务层
│   │   ├── tasks/           # Celery异步任务
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   └── main.py          # 应用入口
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── crawler/                 # 采集服务
│   ├── crawler/
│   │   ├── spiders/         # 爬虫
│   │   ├── pipelines.py     # 数据管道
│   │   ├── middlewares.py   # 中间件
│   │   ├── items.py         # 数据项定义
│   │   ├── settings.py      # 配置
│   │   └── utils/           # 工具函数
│   ├── requirements.txt
│   ├── scrapy.cfg
│   └── Dockerfile
├── frontend/                # 前端Web
│   ├── src/
│   │   ├── api/             # API封装
│   │   ├── components/      # 组件
│   │   ├── router/          # 路由
│   │   ├── store/           # 状态管理
│   │   ├── styles/          # 样式
│   │   ├── utils/           # 工具函数
│   │   ├── views/           # 页面
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf
│   └── Dockerfile
├── deploy/                  # 部署相关
│   └── init.sql             # 数据库初始化脚本
├── docker-compose.yml       # Docker Compose配置
├── .env.example             # 环境变量示例
└── README.md
```

## 功能模块

### 1. 资讯采集模块

- **配置化采集**：通过数据库配置采集渠道，支持CSS选择器配置
- **三层去重**：URL去重 → 内容MD5去重 → 语义去重（V2.0）
- **代理池**：支持Redis代理池，自动检测代理质量
- **调度策略**：全量采集（每日）+ 增量采集（每12小时）+ 重点渠道轮询（每小时）

### 2. AI处理模块

- **规则引擎前置过滤**：快速过滤噪音内容，减少AI调用
- **分类打标**：自动识别业务分类、区域标签、行业标签、资讯类型
- **摘要生成**：自动生成核心摘要
- **业务启示**：生成对公业务营销启示
- **质量评分**：对资讯商机价值进行打分
- **模拟模式**：无API Key时使用规则模拟，保证系统可运行

### 3. 资讯展示模块

- **首页看板**：统计数据 + 多维度筛选 + 资讯列表
- **地图视图**：区域热力图展示（需接入高德地图）
- **详情页**：完整内容 + 业务启示 + 一键上报线索
- **业务专题**：按主题聚合资讯

### 4. 线索管理模块

- **线索上报**：手动录入或资讯一键转化
- **个人池/公海池**：线索保护期机制，到期自动回收
- **跟进记录**：完整跟进历史，每次跟进自动续期
- **状态流转**：新建 → 跟进中 → 已转化 / 已流失 / 已释放

### 5. 每日简报模块

- **自动生成**：每日定时生成当日简报
- **分类展示**：按业务分类分组展示
- **一键推送**：支持推送到企业微信/飞书等

### 6. 用户权限模块

- **四级角色**：admin(管理员) > editor(编辑) > reviewer(审核员) > viewer(普通用户)
- **JWT认证**：Access Token + Refresh Token
- **SSO集成**：支持企业微信/飞书SSO（可选）

## API文档

启动后访问 Swagger UI：http://localhost:8000/docs

主要API分组：
- `/api/v1/auth` - 认证相关
- `/api/v1/news` - 资讯相关
- `/api/v1/leads` - 线索相关
- `/api/v1/briefings` - 简报相关
- `/api/v1/users` - 用户管理

## 配置说明

### AI配置

系统支持两种AI模式：

1. **模拟模式**（默认）：不调用真实API，使用规则引擎模拟，适合开发测试
2. **真实模式**：配置 `AI_API_KEY` 后自动启用，调用大模型API

```bash
# .env 文件中配置
AI_API_KEY=sk-xxx
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-3.5-turbo
```

### 采集渠道配置

采集渠道配置在 `crawl_sources` 表中，支持以下字段：
- `name` - 渠道名称
- `source_type` - 来源类型（gov/bidding/park/enterprise）
- `crawl_type` - 采集类型（list/static/dynamic）
- `entry_url` - 入口URL
- `selector_config` - 选择器配置（JSON格式）
- `crawl_interval_hours` - 采集间隔（小时）
- `priority` - 优先级

### 标签体系

标签在 `tag_dictionary` 表中配置，支持：
- 业务分类标签（deposit/loan/investment_bank/treasury/supply_chain）
- 区域标签
- 行业标签
- 资讯类型标签（policy/bidding/enterprise/park）

## 开发指南

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 修改 DATABASE_URL 和 REDIS_URL 指向本地服务

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

前端开发服务器默认代理 `/api` 到 `http://localhost:8000`。

### 采集服务开发

```bash
cd crawler

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行爬虫
scrapy crawl gov_chaoyang
```

## 部署建议

### 生产环境配置

1. **修改默认密码**：首次启动后立即修改admin密码
2. **JWT密钥**：设置强随机的 `JWT_SECRET_KEY`
3. **数据库密码**：使用强密码
4. **Redis密码**：设置Redis密码
5. **HTTPS**：配置Nginx启用HTTPS
6. **备份**：配置数据库定期备份

### 性能优化

- PostgreSQL：调整 `shared_buffers`、`work_mem` 等参数
- Redis：开启RDB/AOF持久化
- Celery：根据任务量调整worker数量
- Nginx：开启gzip、静态资源缓存

### 监控告警

- 集成 Prometheus + Grafana
- 监控指标：API响应时间、错误率、采集成功率、AI调用量
- 告警规则：服务异常、采集失败率过高、数据库连接数等

## 常见问题

### Q: 启动后前端无法访问后端API？

A: 检查docker-compose中frontend和backend是否在同一网络，确认Nginx配置中的proxy_pass地址正确。

### Q: AI处理不生效？

A: 检查 `AI_API_KEY` 是否配置，未配置时系统使用模拟模式。可查看 `ai_process_logs` 表确认处理状态。

### Q: 采集没有数据？

A: 1. 检查 `crawl_sources` 表中渠道是否启用；2. 查看 `crawl_logs` 表确认采集状态；3. 确认网络连通性。

### Q: 如何添加新的采集渠道？

A: 在 `crawl_sources` 表中插入新记录，配置好 `selector_config`（列表页和详情页的CSS选择器），系统会自动按配置的间隔采集。

## 版本历史

### v1.0.0 (2024-xx-xx)
- 初始版本发布
- 核心功能：资讯采集、AI处理、移动端展示、线索管理、每日简报
- 技术栈：Vue3 + FastAPI + PostgreSQL + Redis + Scrapy

## 许可证

本项目仅供内部使用。

## 联系方式

如有问题，请联系系统管理员。

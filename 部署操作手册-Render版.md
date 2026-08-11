# 对公资讯聚合系统 - Render 部署操作手册

> **推荐方案**：Render 单容器部署 + Supabase 免费 PostgreSQL
> **预计耗时**：10-15 分钟
> **月度成本**：0 元（免费版）/ 约 230 元（正式版）
> **无需本地安装任何软件**，全程网页操作

---

## 📋 目录

1. [方案概述](#方案概述)
2. [前置准备（需注册 3 个账号）](#前置准备)
3. [第一步：上传代码到 Gitee](#第一步上传代码到-gitee)
4. [第二步：创建 Supabase 数据库](#第二步创建-supabase-数据库)
5. [第三步：导入数据库表结构](#第三步导入数据库表结构)
6. [第四步：部署到 Render](#第四步部署到-render)
7. [第五步：验证部署](#第五步验证部署)
8. [第六步：初始化管理员账号](#第六步初始化管理员账号)
9. [常见问题排查](#常见问题排查)
10. [后续优化建议](#后续优化建议)

---

## 方案概述

### 架构说明

采用**单容器部署**方案，前后端打包在一个 Docker 容器中：

```
用户浏览器 → Render 容器（FastAPI 后端 + Vue3 前端静态文件）
                  ↓
            Supabase PostgreSQL（免费云数据库）
```

### 为什么选这个方案？

| 对比项 | Render 单容器 | Docker Compose | 手动部署 |
|--------|-------------|----------------|----------|
| 难度 | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 复杂 |
| 成本 | 免费起 | 服务器费用 | 服务器费用 |
| 需本地环境 | ❌ 不需要 | ✅ 需要Docker | ✅ 需要全套 |
| 部署时间 | 10分钟 | 30分钟 | 2小时+ |
| 自动HTTPS | ✅ 自带 | ❌ 需配置 | ❌ 需配置 |
| 自动更新 | ✅ Git推送即部署 | ❌ 手动 | ❌ 手动 |

### 成本估算

**完全免费方案（适合试用）**
- Render Web Service (Free)：$0/月（15分钟无请求会休眠）
- Supabase (Free)：$0/月（500MB数据库）
- **总计：$0/月**

**低成本正式方案（推荐）**
- Render Web Service (Starter $7) + Supabase (Pro $25)
- **总计：约 $32/月（约 230 元人民币）**

---

## 前置准备

部署前需要注册以下 3 个账号（均可用邮箱注册，免费）：

| 平台 | 用途 | 注册地址 |
|------|------|----------|
| Gitee | 代码托管（国内访问快） | https://gitee.com |
| Supabase | PostgreSQL 云数据库 | https://supabase.com |
| Render | 应用托管平台 | https://render.com |

> 💡 **提示**：Render 也支持 GitHub，如果已有 GitHub 账号可以不用 Gitee。但 Gitee 国内访问更稳定。

---

## 第一步：上传代码到 Gitee

### 方式 A：网页端直接上传（推荐，无需安装 Git）

1. 登录 Gitee：https://gitee.com
2. 点击右上角 **「+」** → **「新建仓库」**
3. 填写仓库信息：
   - **仓库名称**：`gongzi-info-aggregator`
   - **路径**：自动生成即可
   - **开源**：选择「私有」（推荐，代码不公开）
   - **初始化仓库**：**不要勾选**任何选项（不要初始化README、.gitignore等）
4. 点击 **「创建」**
5. 创建后进入仓库页面，点击 **「上传文件」** 按钮
6. 在弹出的页面中，点击 **「选择文件」**
7. 找到本地项目文件夹：
   ```
   D:\python project\对公资讯聚合\对公资讯聚合系统 - 含Render部署配置完整包\gongzi-info-aggregator
   ```
8. **全选文件夹内所有文件和子文件夹**（Ctrl+A），拖拽到上传区域
   - 包括：`.git` 文件夹可以不上传
   - 必须包含：`Dockerfile`、`backend/`、`frontend/`、`deploy/`、`render.yaml` 等
9. 等待上传完成，在下方填写提交信息：`初始提交`
10. 点击 **「提交」**

> ⚠️ **注意**：Gitee 网页上传单文件不能超过 20MB，如果有大文件可能需要用 Git 方式上传。本项目没有大文件，网页上传没问题。

### 方式 B：Git 命令行上传（需先安装 Git）

如果已安装 Git，在项目目录打开命令行执行：

```bash
cd "D:\python project\对公资讯聚合\对公资讯聚合系统 - 含Render部署配置完整包\gongzi-info-aggregator"
git init
git add .
git commit -m "初始提交"
git remote add origin https://gitee.com/你的用户名/gongzi-info-aggregator.git
git push -u origin master
```

### 验证代码上传成功

上传完成后，在 Gitee 仓库页面应能看到以下文件结构：
```
gongzi-info-aggregator/
├── Dockerfile          ← 必须有（根目录）
├── docker-compose.yml
├── render.yaml
├── .env.example
├── backend/
├── frontend/
├── crawler/
├── deploy/
│   └── init.sql        ← 必须有
└── docs/
```

---

## 第二步：创建 Supabase 数据库

1. 登录 Supabase：https://supabase.com
2. 点击右上角 **「Start your project」**（或「New Project」）
3. 用 GitHub 或邮箱注册登录
4. 登录后点击 **「New Project」**
5. 填写项目信息：

   | 字段 | 填写内容 |
   |------|----------|
   | **Name** | `gongzi-info` |
   | **Database Password** | 设一个强密码，**务必记下来**（例如：`Gongzi2024!Safe`） |
   | **Region** | 选择 `Southeast Asia (Singapore)` 新加坡（离国内最近） |
   | **Pricing Plan** | 选择 `Free` 免费版 |

6. 点击 **「Create new project」**
7. 等待创建完成（约 1-2 分钟，页面会显示进度）

### 获取数据库连接串

创建完成后：

1. 左侧菜单点击 **「Project Settings」**（齿轮图标）
2. 点击 **「Database」**
3. 找到 **「Connection string」** 区域
4. 切换到 **「URI」** 标签
5. 复制连接串，格式类似：
   ```
   postgresql://postgres:你的密码@db.xxxx.supabase.co:5432/postgres
   ```
6. **把这串保存好**，后面 Render 配置要用

> 💡 注意：连接串中的 `你的密码` 部分会自动填充，直接复制完整的即可。

---

## 第三步：导入数据库表结构

1. 在 Supabase 左侧菜单点击 **「SQL Editor」**
2. 点击 **「New query」** → 「New blank query」
3. 打开本地文件：
   ```
   D:\python project\对公资讯聚合\对公资讯聚合系统 - 含Render部署配置完整包\gongzi-info-aggregator\deploy\init.sql
   ```
4. **全选文件内容**（Ctrl+A），复制
5. 粘贴到 Supabase 的 SQL Editor 编辑框中
6. 点击右下角 **「Run」** 或按 `Ctrl+Enter` 执行
7. 等待执行完成，下方显示 `Success. No rows returned` 即表示成功

### 验证表创建成功

1. 左侧菜单点击 **「Table Editor」**
2. 应能看到以下表：
   - `users` - 用户表
   - `tag_dictionary` - 标签字典
   - `crawl_sources` - 采集渠道
   - `news_items` - 资讯主表
   - `leads` - 线索表
   - `briefings` - 简报表
   - 等等...

---

## 第四步：部署到 Render

### 4.1 创建 Web Service

1. 登录 Render：https://render.com
2. 点击右上角 **「New +」** → **「Web Service」**
3. 连接代码仓库：
   - 如果用 GitHub：点击 **「Connect GitHub」**，授权后选择你的仓库
   - 如果用 Gitee：选择 **「Public Git repository」**，填入 Gitee 仓库地址
     - 格式：`https://gitee.com/你的用户名/gongzi-info-aggregator.git`
     - ⚠️ Gitee 私有仓库可能无法直接连接，建议设为公开，或用 GitHub

4. 点击 **「Continue」**

### 4.2 配置服务参数

在下一页填写以下配置：

| 配置项 | 填写内容 |
|--------|----------|
| **Name** | `gongzi-info`（会成为子域名，如 gongzi-info.onrender.com） |
| **Region** | 选择 `Singapore` 新加坡 |
| **Runtime** | 选择 `Docker` |
| **Dockerfile Path** | `Dockerfile`（根目录的那个，**不是** backend/Dockerfile） |
| **Docker Context** | 留空（默认根目录） |
| **Branch** | `master`（或 `main`，看你的默认分支） |
| **Plan** | 选择 `Free` 免费版（或 `Starter` $7/月） |

### 4.3 配置环境变量

点击 **「Advanced」** 展开高级选项，然后点击 **「Add Environment Variable」**，逐一添加：

| Key | Value | 说明 |
|-----|-------|------|
| `DATABASE_URL` | 第二步获取的 Supabase 连接串 | **必填** |
| `SECRET_KEY` | 随机字符串，至少32位 | **必填**，JWT加密密钥 |
| `APP_ENV` | `production` | 运行环境 |
| `CORS_ORIGINS` | `*` | 允许跨域 |
| `AI_API_KEY` | （可选）你的大模型API Key | 不填则用模拟模式 |

> 🔑 **生成 SECRET_KEY**：可以随便敲一串，例如 `GongziInfo2024SecretKeyForJWTEncryptionx9f2k`
>
> 也可以用在线工具生成：https://www.sexauth.com/tool/random-string

### 4.4 设置健康检查

在 Advanced 区域找到 **「Health Check Path」**，填入：
```
/health
```

### 4.5 开始部署

点击底部 **「Create Web Service」**

Render 会开始：
1. 拉取代码
2. 构建 Docker 镜像（前端 npm build + 后端 pip install）
3. 部署容器

**第一次构建约需 5-10 分钟**，请耐心等待。页面会实时显示构建日志。

---

## 第五步：验证部署

### 5.1 查看部署状态

在 Render 服务详情页，顶部显示：
- 🟢 **Live**：部署成功
- 🟡 **In Progress**：正在部署
- 🔴 **Deploy Failed**：部署失败

### 5.2 访问系统

部署成功后，会得到一个域名，例如：
```
https://gongzi-info.onrender.com
```

依次访问以下地址验证：

| 地址 | 预期结果 |
|------|----------|
| `https://你的服务名.onrender.com/health` | 返回 `{"status":"ok",...}` |
| `https://你的服务名.onrender.com/docs` | 显示 Swagger API 文档 |
| `https://你的服务名.onrender.com` | 显示前端登录页面 |

> ⚠️ **免费版注意**：如果 15 分钟没有访问，服务会休眠。首次访问需要等待 30-60 秒唤醒。

---

## 第六步：初始化管理员账号

数据库表结构已导入，但还没有用户账号。需要通过 API 创建管理员。

### 方式 A：通过 Swagger 文档创建

1. 访问 `https://你的服务名.onrender.com/docs`
2. 找到 `POST /api/v1/auth/register` 接口
3. 点击 **「Try it out」**
4. 填写请求体：
   ```json
   {
     "username": "admin",
     "password": "admin123",
     "full_name": "管理员",
     "email": "admin@example.com"
   }
   ```
5. 点击 **「Execute」**
6. 返回 `200` 即表示创建成功

### 方式 B：通过后端初始化脚本

如果注册接口不可用，可以在 Render 的 Shell 中执行：

1. Render 服务页面点击 **「Shell」** 标签
2. 执行：
   ```bash
   python init_db.py
   ```
3. 脚本会自动创建默认管理员账号

### 登录系统

1. 访问 `https://你的服务名.onrender.com`
2. 使用账号登录：
   - 用户名：`admin`
   - 密码：`admin123`
3. **登录后立即修改密码！**（个人设置 → 修改密码）

---

## 常见问题排查

### Q1: Render 部署失败，日志显示 npm 错误

**可能原因**：前端 TypeScript 类型检查失败

**解决方案**：
1. 修改 `frontend/package.json`，将 build 命令改为：
   ```json
   "build": "vite build"
   ```
   （去掉 `vue-tsc &&`，跳过类型检查）
2. 提交代码到 Gitee，Render 会自动重新部署

### Q2: 部署成功但页面空白

**可能原因**：前端静态文件未正确挂载

**排查步骤**：
1. 访问 `/docs` 看后端是否正常
2. 查看 Render 日志，确认前端构建成功
3. 确认根目录 `Dockerfile` 被使用（不是 backend/Dockerfile）

### Q3: 数据库连接失败

**可能原因**：Supabase 连接串错误或 IP 白名单限制

**解决方案**：
1. 检查 `DATABASE_URL` 是否正确
2. Supabase → Settings → Database → 确认 IP 允许列表包含 `0.0.0.0/0`
3. 密码中如有特殊字符，需要 URL 编码

### Q4: 免费版休眠后唤醒慢

**解决方案**：
- 升级到 Render Starter 套餐（$7/月），不会休眠
- 或使用 UptimeRobot 等监控服务定时访问（每5分钟一次），保持唤醒

### Q5: 如何更新代码？

1. 修改本地代码
2. 上传到 Gitee（覆盖上传或 Git push）
3. Render 会**自动检测到更新并重新部署**
4. 也可以在 Render 页面手动点击 **「Manual Deploy」** → **「Latest commit」**

### Q6: 如何查看日志？

- Render 服务页面 → **「Logs」** 标签
- 实时显示应用输出和错误信息

---

## 后续优化建议

### 安全加固（部署后立即做）

1. ✅ 修改默认管理员密码
2. ✅ 设置强 `SECRET_KEY`
3. ✅ Supabase 数据库密码使用强密码
4. ⬜ 将 `CORS_ORIGINS` 改为你的域名（如 `https://gongzi-info.onrender.com`）

### 功能增强

1. **配置 AI API Key**：在 Render 环境变量添加 `AI_API_KEY`，启用真实 AI 处理
   - 支持 OpenAI、DeepSeek、智谱等兼容 OpenAI 格式的 API
   - 同时设置 `AI_BASE_URL` 和 `AI_MODEL`

2. **添加采集渠道**：在数据库 `crawl_sources` 表中添加政府网站、招投标平台等

3. **配置 Redis**（可选）：
   - Render 可以创建 Redis 服务（免费版有限）
   - 添加 `REDIS_URL` 环境变量

4. **自定义域名**：
   - Render → Settings → Custom Domains
   - 添加你的域名，按提示配置 DNS

### 备份策略

- Supabase 免费版每天自动备份（保留 7 天）
- 定期导出数据库：Supabase → Settings → Database → Dump

### 监控告警

- Render 自带基础监控（CPU、内存、响应时间）
- 可接入 UptimeRobot 做可用性监控（免费）

---

## 附录：环境变量完整清单

| 变量名 | 必填 | 说明 | 示例值 |
|--------|------|------|--------|
| `DATABASE_URL` | ✅ | PostgreSQL连接串 | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | ✅ | JWT加密密钥 | 随机32位字符串 |
| `APP_ENV` | ❌ | 运行环境 | `production` |
| `CORS_ORIGINS` | ❌ | 允许跨域域名 | `*` 或具体域名 |
| `REDIS_URL` | ❌ | Redis连接串 | `redis://host:6379/0` |
| `AI_API_KEY` | ❌ | 大模型API Key | `sk-xxx` |
| `AI_BASE_URL` | ❌ | 大模型API地址 | `https://api.openai.com/v1` |
| `AI_MODEL` | ❌ | 模型名称 | `gpt-3.5-turbo` |
| `CELERY_BROKER_URL` | ❌ | Celery代理 | `redis://host:6379/1` |
| `CELERY_RESULT_BACKEND` | ❌ | Celery结果后端 | `redis://host:6379/2` |

---

## 联系与支持

如遇问题，请检查：
1. Render 日志（最关键）
2. Supabase 数据库连接
3. 环境变量是否正确填写

部署成功后，默认访问地址：
- 前端：`https://你的服务名.onrender.com`
- API文档：`https://你的服务名.onrender.com/docs`
- 健康检查：`https://你的服务名.onrender.com/health`

---

*手册版本：v1.0 | 更新日期：2026-08-11*

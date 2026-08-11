# 对公资讯聚合系统 - Render 部署指南

## 🚀 快速部署（10分钟搞定）

### 第一步：上传代码到 Gitee

1. 登录 Gitee：https://gitee.com
2. 点击右上角「+」→ 「新建仓库」
3. 仓库名称：`gongzi-info-aggregator`
4. 选择「公开」或「私有」都可以
5. 点击「创建」

然后在本地（或服务器）执行：

```bash
# 进入项目目录
cd gongzi-info-aggregator

# 初始化 git
git init
git add .
git commit -m "初始提交"

# 添加远程仓库（替换成你的Gitee地址）
git remote add origin https://gitee.com/你的用户名/gongzi-info-aggregator.git

# 推送代码
git push -u origin master
```

---

### 第二步：创建 Supabase 数据库（免费PostgreSQL）

1. 登录 Supabase：https://supabase.com
2. 点击「New Project」
3. 填写信息：
   - Name: `gongzi-info`
   - Database Password: 自己设一个密码（记下来）
   - Region: 选新加坡或东京（离国内近）
   - Plan: Free
4. 点击「Create new project」
5. 等待创建完成（约2分钟）

6. 导入数据库表结构：
   - 左侧菜单选择「SQL Editor」
   - 点击「New query」
   - 把 `deploy/init.sql` 的内容复制进去
   - 点击「Run」执行

7. 获取数据库连接串：
   - 左侧菜单选择「Settings」→ 「Database」
   - 找到「Connection string」→ 「URI」
   - 复制下来，格式类似：
     ```
     postgresql://postgres:xxxx@db.xxxx.supabase.co:5432/postgres
     ```

---

### 第三步：部署到 Render

#### 方式A：单容器部署（推荐，更简单）

1. 登录 Render：https://render.com
2. 点击右上角「New +」→ 「Web Service」
3. 选择「Connect Git」→ 连接你的 Gitee 仓库
   - 如果Gitee连接不了，可以先把代码同步到GitHub，或者用Public Git URL方式
   - Public Git URL 填写你的Gitee仓库克隆地址

4. 配置信息：
   - Name: `gongzi-info`（随便起，会成为子域名）
   - Runtime: `Docker`
   - Dockerfile Path: `Dockerfile`（根目录的那个）
   - Region: 选 Singapore（新加坡，离国内近）
   - Plan: Free（免费版）

5. 点击「Advanced」→ 「Add Environment Variable」，添加以下环境变量：

   | Key | Value | 说明 |
   |-----|-------|------|
   | `DATABASE_URL` | 你的Supabase连接串 | PostgreSQL数据库地址 |
   | `SECRET_KEY` | 随便输一串随机字符 | JWT加密密钥 |
   | `APP_ENV` | `production` | 运行环境 |
   | `AI_API_KEY` | （可选）你的大模型API Key | 不填则使用模拟模式 |
   | `CORS_ORIGINS` | `*` | 允许跨域的域名 |

6. 点击「Create Web Service」
7. 等待部署完成（第一次约5-10分钟）

8. 部署完成后，你会得到一个域名，比如：
   ```
   https://gongzi-info.onrender.com
   ```
   直接访问就能用了！

---

#### 方式B：前后端分离部署（更灵活）

如果你想前后端分开部署，可以用 `render.yaml` 一键部署：

1. 在 Render Dashboard 点击「New +」→ 「Deploy from YAML」
2. 选择你的仓库
3. 选择 `render.yaml` 文件
4. 修改里面的仓库地址为你的Gitee地址
5. 点击「Apply」

这样会自动创建：
- 后端服务（gongzi-backend）
- 前端静态站点（gongzi-frontend）
- Redis 缓存
- PostgreSQL 数据库

---

## 📋 环境变量说明

| 变量名 | 必填 | 说明 | 默认值 |
|--------|------|------|--------|
| `DATABASE_URL` | ✅ | PostgreSQL数据库连接串 | - |
| `SECRET_KEY` | ✅ | JWT加密密钥，生产环境务必修改 | - |
| `REDIS_URL` | ❌ | Redis连接串，不填则用内存缓存 | - |
| `AI_API_KEY` | ❌ | 大模型API Key，不填则用模拟模式 | - |
| `AI_BASE_URL` | ❌ | 大模型API地址 | OpenAI官方地址 |
| `AI_MODEL` | ❌ | 模型名称 | gpt-3.5-turbo |
| `APP_ENV` | ❌ | 运行环境 | production |
| `CORS_ORIGINS` | ❌ | 允许跨域的域名，逗号分隔 | * |
| `API_V1_PREFIX` | ❌ | API前缀 | /api/v1 |

---

## 🔧 常见问题

### Q: 免费版会不会休眠？
A: Render免费版15分钟没有请求会休眠，首次访问需要等几十秒唤醒。正式使用建议升级到Starter套餐（$7/月）。

### Q: Supabase免费版有什么限制？
A: 500MB数据库空间，每月1GB带宽，足够初期使用。

### Q: 怎么更新代码？
A: 直接push到Git仓库，Render会自动重新部署。

### Q: 怎么查看日志？
A: 在Render的服务详情页，点击「Logs」标签。

### Q: 国内访问速度怎么样？
A: 新加坡节点访问速度还可以，大概100-300ms延迟。如果需要更快，可以用国内云服务商。

---

## 📱 访问地址

部署成功后：
- **前端页面**：https://你的服务名.onrender.com
- **API文档**：https://你的服务名.onrender.com/docs
- **健康检查**：https://你的服务名.onrender.com/health

默认账号：
- 管理员：`admin` / `admin123`
- 普通用户：`user` / `user123`

⚠️ **首次登录后请立即修改默认密码！**

---

## 💰 成本估算

### 完全免费方案
- Render Web Service (Free)：$0/月
- Supabase (Free)：$0/月
- **总计：$0/月**
- 限制：会休眠，资源有限，适合试用

### 低成本方案（推荐正式使用）
- Render Web Service (Starter)：$7/月
- Supabase (Pro)：$25/月
- **总计：约$32/月（约230元人民币）**
- 无限运行时间，10GB数据库，足够小团队使用

### 国内方案
- 阿里云轻量应用服务器（2核2G）：约30-50元/月
- 云数据库 PostgreSQL：约30元/月
- **总计：约60-80元/月**
- 国内访问速度快，备案后可用国内域名

---

## 🚀 下一步

部署成功后，你可以：
1. 修改默认密码
2. 配置AI API Key启用真实AI处理
3. 添加采集渠道配置
4. 配置自定义域名
5. 设置监控告警

有任何问题随时问我！

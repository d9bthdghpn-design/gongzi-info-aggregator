-- ============================================================
-- 对公资讯聚合系统 - 线上数据库补丁（第 1 步）
-- 修复登录 500 错误：users 表缺少 password_hash 列
-- 适用：已在 Supabase 执行过旧版 init.sql 的数据库
-- 用法：复制全部内容到 Supabase → SQL Editor → Run
-- ============================================================

-- 1. 给 users 表补充 password_hash 列（如果不存在）
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(256) NOT NULL DEFAULT '';

-- 2. 验证列是否添加成功（应能看到 password_hash 这一行）
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'users'
ORDER BY ordinal_position;

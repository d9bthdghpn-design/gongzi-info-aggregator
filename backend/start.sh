#!/bin/bash
# 对公资讯聚合系统 - 容器启动脚本
# 自动初始化数据库 + 启动后端服务

set -e

echo "=========================================="
echo "  对公资讯聚合系统 - 启动中..."
echo "=========================================="

# 等待数据库就绪（最多等30秒）
echo "[$(date '+%H:%M:%S')] 等待数据库就绪..."
for i in $(seq 1 30); do
    python -c "
import os, sys
try:
    from app.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('数据库连接成功')
    sys.exit(0)
except Exception as e:
    print(f'等待数据库... ({e})')
    sys.exit(1)
" && break || sleep 1
done

# 初始化数据库（幂等，安全重复执行）
echo "[$(date '+%H:%M:%S')] 初始化数据库..."
python init_db.py || echo "警告: 数据库初始化出现问题，继续启动..."

# 启动后端服务
echo "[$(date '+%H:%M:%S')] 启动 FastAPI 服务..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

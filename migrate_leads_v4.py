"""
v4 leads表迁移：新增source_category、estimated_amount、converted_amount字段
"""
import os
import sys

os.environ.setdefault("DATABASE_URL", "postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("JWT_SECRET_KEY", "gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH")
os.environ.setdefault("CORS_ORIGINS", "https://gongzi-info-aggregator.onrender.com")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.database import engine
from sqlalchemy import text


def migrate():
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'leads' AND column_name = 'source_category'
        """))
        if result.fetchone():
            print("source_category字段已存在，跳过")
        else:
            conn.execute(text("ALTER TABLE leads ADD COLUMN source_category VARCHAR(64)"))
            print("已添加 source_category 字段")

        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'leads' AND column_name = 'estimated_amount'
        """))
        if result.fetchone():
            print("estimated_amount字段已存在，跳过")
        else:
            conn.execute(text("ALTER TABLE leads ADD COLUMN estimated_amount NUMERIC(18,2)"))
            print("已添加 estimated_amount 字段")

        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'leads' AND column_name = 'converted_amount'
        """))
        if result.fetchone():
            print("converted_amount字段已存在，跳过")
        else:
            conn.execute(text("ALTER TABLE leads ADD COLUMN converted_amount NUMERIC(18,2)"))
            print("已添加 converted_amount 字段")

        conn.commit()
        print("\nleads表迁移完成！")


if __name__ == "__main__":
    migrate()

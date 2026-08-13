"""数据库迁移脚本 - 添加7维评分字段和事件聚类表
执行方式: python migrate_v2_7dim_cluster.py
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ["DATABASE_URL"] = "postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
os.environ["ENVIRONMENT"] = "production"
os.environ["JWT_SECRET_KEY"] = "migrate-key-v2"

from app.database import engine
from sqlalchemy import text


def migrate():
    print("=" * 60)
    print("数据库迁移 V2 - 7维评分 + 事件聚类")
    print("=" * 60)

    with engine.connect() as conn:
        # 1. 添加 score_dimensions 字段
        print("\n[1] 检查并添加 score_dimensions 字段...")
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'news_items' AND column_name = 'score_dimensions'
        """))
        if result.fetchone():
            print("  score_dimensions 字段已存在，跳过")
        else:
            conn.execute(text("""
                ALTER TABLE news_items ADD COLUMN score_dimensions JSON DEFAULT '{}'::json
            """))
            print("  ✓ 已添加 score_dimensions 字段")

        # 2. 添加 event_cluster_id 字段
        print("\n[2] 检查并添加 event_cluster_id 字段...")
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'news_items' AND column_name = 'event_cluster_id'
        """))
        if result.fetchone():
            print("  event_cluster_id 字段已存在，跳过")
        else:
            conn.execute(text("""
                ALTER TABLE news_items ADD COLUMN event_cluster_id VARCHAR(36)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_news_items_event_cluster_id ON news_items(event_cluster_id)
            """))
            print("  ✓ 已添加 event_cluster_id 字段及索引")

        # 3. 创建 event_clusters 表
        print("\n[3] 检查并创建 event_clusters 表...")
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'event_clusters'
        """))
        if result.fetchone():
            print("  event_clusters 表已存在，跳过")
        else:
            conn.execute(text("""
                CREATE TABLE event_clusters (
                    id VARCHAR(36) PRIMARY KEY,
                    title VARCHAR(512) NOT NULL,
                    description TEXT,
                    event_type VARCHAR(32),
                    news_count INTEGER DEFAULT 0,
                    news_ids JSON DEFAULT '[]'::json,
                    source_channels JSON DEFAULT '[]'::json,
                    first_publish_date DATE,
                    last_publish_date DATE,
                    max_quality_score INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_event_clusters_event_type ON event_clusters(event_type)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_event_clusters_first_publish_date ON event_clusters(first_publish_date)
            """))
            print("  ✓ 已创建 event_clusters 表及索引")

        conn.commit()

    # 4. 验证
    print("\n[4] 验证迁移结果...")
    with engine.connect() as conn:
        # 检查字段
        cols = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'news_items' AND column_name IN ('score_dimensions', 'event_cluster_id')
        """)).fetchall()
        print(f"  news_items 新字段: {[c[0] for c in cols]}")

        # 检查表
        tables = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'event_clusters'
        """)).fetchall()
        print(f"  新表: {[t[0] for t in tables]}")

        # 统计现有数据
        total = conn.execute(text("SELECT COUNT(*) FROM news_items")).fetchone()[0]
        print(f"  现有资讯数据: {total} 条（不受迁移影响）")

    print("\n" + "=" * 60)
    print("迁移完成！")
    print("=" * 60)


if __name__ == "__main__":
    migrate()

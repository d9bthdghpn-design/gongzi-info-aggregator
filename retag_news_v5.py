"""
v5 标签增量打标脚本
====================
只处理 topic_tags 为空（NULL 或 []）的资讯，补齐 v5 四维标签：
business_category / topic_tags / industry_tags / area_tags / info_type
已打标数据不受影响，可安全地在每日采集后运行。

用法: python retag_news_v5.py
"""
import os
import sys
import re
from collections import Counter

os.environ.setdefault("DATABASE_URL", "postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("JWT_SECRET_KEY", "gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH")
os.environ.setdefault("CORS_ORIGINS", "https://gongzi-info-aggregator.onrender.com")

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "backend"))

from sqlalchemy import text
from sqlalchemy.orm.attributes import flag_modified
from upgrade_tags_v5 import tag_item, MOCK_TIPS
from app.database import SessionLocal
from app.models import NewsItem


def main():
    db = SessionLocal()
    try:
        # 找出缺少 topic_tags 的资讯（NULL 或空数组）
        items = db.query(NewsItem).filter(
            NewsItem.is_deleted == False,
            text("(topic_tags IS NULL OR topic_tags = '[]'::jsonb OR topic_tags = 'null'::jsonb)"),
        ).all()

        print(f"== v5 增量打标: 待处理 {len(items)} 条 ==")
        if not items:
            print("无新增待打标数据，跳过")
            return

        updated = 0
        tip_cleaned = 0
        after_action = Counter()
        after_topic = Counter()

        for it in items:
            new = tag_item(it.title or "", it.content_summary or "", it.content_raw or "", it.source_channel or "")
            it.business_category = new["business_category"]
            it.topic_tags = new["topic_tags"]
            it.industry_tags = new["industry_tags"]
            it.area_tags = new["area_tags"]
            it.info_type = new["info_type"]
            if it.business_tip and it.business_tip.strip() in MOCK_TIPS:
                it.business_tip = None
                tip_cleaned += 1
            flag_modified(it, "industry_tags")
            flag_modified(it, "area_tags")
            flag_modified(it, "topic_tags")
            updated += 1
            after_action[new["business_category"]] += 1
            for t in new["topic_tags"]:
                after_topic[t] += 1

        db.commit()

        print(f"完成: 打标 {updated} 条 | 清理模拟废话 tip {tip_cleaned} 条")
        print("\naction 分布:", dict(after_action))
        print("topic TOP10:", dict(after_topic.most_common(10)))
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

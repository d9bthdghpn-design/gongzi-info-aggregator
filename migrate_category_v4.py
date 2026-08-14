"""
v4分类迁移脚本：旧v3分类 → 新v4行动分类
映射规则：
- bidding_procurement → bid_action
- policy_regulation → policy_ref
- industry_economy → park_project
- enterprise_dynamics → 默认fin_demand（含"新设/注册/成立/变更/开户"关键词→account_chance）
- financial_market → fin_demand
"""
import os
import sys

# 设置环境变量
os.environ.setdefault("DATABASE_URL", "postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("JWT_SECRET_KEY", "gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH")
os.environ.setdefault("CORS_ORIGINS", "https://gongzi-info-aggregator.onrender.com")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.database import SessionLocal
from app.models import NewsItem

# 旧→新分类映射
CATEGORY_MAP = {
    "bidding_procurement": "bid_action",
    "policy_regulation": "policy_ref",
    "industry_economy": "park_project",
    "financial_market": "fin_demand",
    # enterprise_dynamics 需要根据内容判断
}

# account_chance关键词
ACCOUNT_KEYWORDS = ["新设", "注册", "成立", "变更", "开户", "迁移", "入驻", "落户", "登记"]


def migrate():
    db = SessionLocal()
    try:
        # 获取所有有旧分类的资讯
        old_cats = list(CATEGORY_MAP.keys()) + ["enterprise_dynamics"]
        items = db.query(NewsItem).filter(
            NewsItem.business_category.in_(old_cats)
        ).all()

        print(f"找到 {len(items)} 条需要迁移的资讯")

        updated = 0
        account_count = 0
        fin_count = 0

        for item in items:
            old_cat = item.business_category
            new_cat = None

            if old_cat == "enterprise_dynamics":
                # 根据内容判断
                text = (item.title or "") + (item.content_raw or "") + (item.content_summary or "")
                if any(kw in text for kw in ACCOUNT_KEYWORDS):
                    new_cat = "account_chance"
                    account_count += 1
                else:
                    new_cat = "fin_demand"
                    fin_count += 1
            else:
                new_cat = CATEGORY_MAP.get(old_cat)

            if new_cat:
                item.business_category = new_cat
                updated += 1
                if updated % 50 == 0:
                    print(f"  已迁移 {updated} 条...")

        db.commit()

        # 统计新分类分布
        print(f"\n迁移完成！共更新 {updated} 条")
        print(f"  enterprise_dynamics → account_chance: {account_count} 条")
        print(f"  enterprise_dynamics → fin_demand: {fin_count} 条")

        # 输出新分类分布
        from sqlalchemy import func
        dist = db.query(
            NewsItem.business_category,
            func.count(NewsItem.id)
        ).group_by(NewsItem.business_category).all()
        print("\n新分类分布：")
        for cat, cnt in dist:
            print(f"  {cat}: {cnt} 条")

    except Exception as e:
        db.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()

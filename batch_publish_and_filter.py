"""
批量处理脚本：
1. 将所有 pending_review 资讯改为 published（取消审核）
2. 基于规则过滤与银行业务明显无关的资讯，标记为 rejected
"""
import os
import sys
from datetime import date

# 设置环境变量（生产环境必须）
os.environ.setdefault("DATABASE_URL", "postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("JWT_SECRET_KEY", "gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH")
os.environ.setdefault("CORS_ORIGINS", "https://gongzi-info-aggregator.onrender.com")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.database import SessionLocal
from app.models import NewsItem

# 噪音关键词（与银行业务完全无关的内容）
NOISE_KEYWORDS = [
    "招聘", "求职", "简历", "广告", "推广", "优惠", "促销",
    "娱乐", "八卦", "明星", "综艺", "游戏", "体育",
    "天气", "星座", "运势", "美食", "旅游攻略", "穿搭",
    "母婴", "育儿经验", "情感", "相亲",
]

# 银行业务相关关键词（命中任一即认为相关）
BANK_RELEVANT_KEYWORDS = [
    # 金融监管
    "金融", "银行", "央行", "人民银行", "银保监", "证监会", "外汇",
    "货币政策", "利率", "LPR", "存款准备金", "流动性",
    # 企业融资
    "融资", "贷款", "信贷", "授信", "担保", "发债", "上市", "IPO",
    "并购", "重组", "增资", "股权", "投资", "基金",
    # 财政税收
    "财政", "税收", "减税", "退税", "补贴", "专项资金", "预算",
    # 产业政策
    "政策", "规划", "产业", "园区", "经开区", "高新区", "示范区",
    "创新", "科技", "数字经济", "人工智能", "新能源", "生物医药",
    # 招投标采购
    "招标", "投标", "采购", "中标", "公告", "项目", "建设", "工程",
    # 区域经济
    "GDP", "经济", "营商环境", "企业", "中小微", "民营", "国企",
    "国资委", "发改委", "经信", "科委", "商务",
    # 银行业务场景
    "结算", "财资", "投行", "供应链", "普惠", "跨境", "汇率",
    "存款", "对公", "客户经理", "商机",
]


def is_bank_relevant(title: str, content: str) -> bool:
    """基于关键词规则判断是否与银行业务相关"""
    text = (title + (content or "")).lower()

    # 命中任一银行相关关键词即认为相关
    for kw in BANK_RELEVANT_KEYWORDS:
        if kw.lower() in text:
            return True

    # 未命中相关关键词，检查是否纯噪音
    for kw in NOISE_KEYWORDS:
        if kw.lower() in text:
            return False

    # 既无相关词也无噪音词，默认保留（来源均为政府官网，大概率相关）
    return True


def main():
    db = SessionLocal()
    try:
        # ===== 步骤1：批量发布 pending_review =====
        pending = db.query(NewsItem).filter(
            NewsItem.status == "pending_review",
            NewsItem.is_deleted == False,
        ).all()
        print(f"待审核资讯数量: {len(pending)}")

        published_count = 0
        for news in pending:
            # 先判断业务相关性
            if not is_bank_relevant(news.title, news.content_raw or news.content_summary or ""):
                news.status = "rejected"
                print(f"  [过滤] {news.title[:40]}... -> rejected")
            else:
                news.status = "published"
                published_count += 1
        db.commit()
        print(f"已发布: {published_count} 条")
        print(f"已过滤(rejected): {len(pending) - published_count} 条")

        # ===== 步骤2：扫描已发布资讯，过滤明显无关的 =====
        published = db.query(NewsItem).filter(
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        ).all()
        print(f"\n已发布资讯数量: {len(published)}")

        rejected_count = 0
        for news in published:
            if not is_bank_relevant(news.title, news.content_raw or news.content_summary or ""):
                news.status = "rejected"
                rejected_count += 1
                print(f"  [过滤] {news.title[:40]}... -> rejected")
        db.commit()
        print(f"从已发布中过滤: {rejected_count} 条")

        # ===== 统计最终状态 =====
        print("\n===== 最终状态统计 =====")
        for status in ["published", "pending_review", "rejected", "ai_failed"]:
            count = db.query(NewsItem).filter(
                NewsItem.status == status,
                NewsItem.is_deleted == False,
            ).count()
            print(f"  {status}: {count} 条")

        total = db.query(NewsItem).filter(NewsItem.is_deleted == False).count()
        print(f"  总计: {total} 条")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

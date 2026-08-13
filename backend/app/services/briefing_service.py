"""
简报服务 - 每日简报生成与管理
"""
from datetime import datetime, date, timezone
from typing import Optional, List
from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session

from app.models import DailyBriefing, NewsItem, TagDictionary
from app.schemas.briefing import BriefingGenerateSchema
from app.core.exceptions import BusinessException


class BriefingService:
    """简报服务"""

    def get_briefing_by_date(self, db: Session, brief_date: date) -> Optional[DailyBriefing]:
        """按日期获取简报"""
        return db.query(DailyBriefing).filter(
            DailyBriefing.brief_date == brief_date
        ).first()

    def generate_briefing(self, db: Session, brief_date: date = None, area_scope: str = None) -> DailyBriefing:
        """生成每日简报"""
        if not brief_date:
            brief_date = date.today()

        # 检查是否已存在
        existing = self.get_briefing_by_date(db, brief_date)
        if existing:
            return existing

        # 获取当天的已发布资讯
        news_list = db.query(NewsItem).filter(
            NewsItem.publish_date == brief_date,
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        ).order_by(desc(NewsItem.quality_score)).all()

        # 获取业务分类标签
        business_tags = db.query(TagDictionary).filter(
            TagDictionary.tag_type == "business",
            TagDictionary.is_active == True,
        ).order_by(TagDictionary.sort_order).all()

        # 按业务分类分组
        category_icons = {
            "deposit": "💰",
            "loan": "🏦",
            "investment_bank": "📈",
            "treasury": "💎",
            "supply_chain": "🔗",
        }

        categories = {}
        category_counts = {}
        total_count = len(news_list)

        for tag in business_tags:
            categories[tag.tag_code] = {
                "category_code": tag.tag_code,
                "category_name": tag.tag_name,
                "icon": category_icons.get(tag.tag_code, "📋"),
                "count": 0,
                "items": [],
            }

        # 其他分类
        categories["other"] = {
            "category_code": "other",
            "category_name": "其他资讯",
            "icon": "📰",
            "count": 0,
            "items": [],
        }

        # 分类整理
        for news in news_list:
            category = news.business_category or "other"
            if category not in categories:
                category = "other"

            categories[category]["count"] += 1
            categories[category]["items"].append({
                "id": str(news.id),
                "title": news.title,
                "summary": news.content_summary or "",
                "business_tip": news.business_tip or "",
                "info_type": news.info_type,
                "quality_score": news.quality_score,
                "area_tags": news.area_tags,
                "industry_tags": news.industry_tags,
                "source_channel": news.source_channel or "",
                "publish_date": news.publish_date.isoformat() if news.publish_date else "",
            })

            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1

        # 只保留有内容的分类
        content_categories = [cat for cat in categories.values() if cat["count"] > 0]

        # 构建简报内容
        content_json = {
            "date": brief_date.isoformat(),
            "total_count": total_count,
            "high_value_count": sum(1 for n in news_list if n.quality_score >= 80),
            "categories": content_categories,
        }

        # 创建简报
        briefing = DailyBriefing(
            brief_date=brief_date,
            area_scope=area_scope,
            content_json=content_json,
            total_count=total_count,
            category_counts=category_counts,
            is_pushed=False,
        )

        db.add(briefing)
        db.commit()
        db.refresh(briefing)
        return briefing

    def push_briefing(self, db: Session, briefing_id: str) -> DailyBriefing:
        """推送简报"""
        briefing = db.query(DailyBriefing).filter(DailyBriefing.id == briefing_id).first()
        if not briefing:
            raise BusinessException(code=404, message="简报不存在")

        briefing.is_pushed = True
        briefing.pushed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(briefing)
        return briefing

    def get_latest_briefings(self, db: Session, limit: int = 7) -> List[DailyBriefing]:
        """获取最近的简报列表"""
        return db.query(DailyBriefing).order_by(desc(DailyBriefing.brief_date)).limit(limit).all()


# 服务单例
briefing_service = BriefingService()

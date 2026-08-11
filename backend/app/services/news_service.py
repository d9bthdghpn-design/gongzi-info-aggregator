"""
资讯服务 - 核心业务逻辑
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import array

from app.models import NewsItem, TagDictionary, Topic
from app.schemas.news import (
    NewsItemCreateSchema, NewsItemUpdateSchema, NewsQuerySchema,
    NewsStatsSchema, TagSchema,
)
from app.services.base import CRUDBase
from app.core.exceptions import BusinessException


class NewsService(CRUDBase[NewsItem, NewsItemCreateSchema, NewsItemUpdateSchema]):
    """资讯服务"""

    def __init__(self):
        super().__init__(NewsItem)

    def get_news_list(
        self, db: Session, query_params: NewsQuerySchema, is_admin: bool = False
    ) -> Tuple[List[NewsItem], int]:
        """获取资讯列表"""
        query = db.query(NewsItem).filter(NewsItem.is_deleted == False)

        # 关键词搜索
        if query_params.keyword:
            keyword = f"%{query_params.keyword}%"
            query = query.filter(
                or_(
                    NewsItem.title.ilike(keyword),
                    NewsItem.content_summary.ilike(keyword),
                )
            )

        # 业务分类筛选
        if query_params.business_category:
            query = query.filter(NewsItem.business_category == query_params.business_category)

        # 区域标签筛选（JSONB数组包含）
        if query_params.area_tags:
            query = query.filter(NewsItem.area_tags.contains(query_params.area_tags))

        # 行业标签筛选
        if query_params.industry_tags:
            query = query.filter(NewsItem.industry_tags.contains(query_params.industry_tags))

        # 资讯类型筛选
        if query_params.info_type:
            query = query.filter(NewsItem.info_type == query_params.info_type)

        # 状态筛选
        if query_params.status:
            query = query.filter(NewsItem.status == query_params.status)

        # 时间范围筛选
        if query_params.start_date:
            query = query.filter(NewsItem.publish_date >= query_params.start_date)
        if query_params.end_date:
            query = query.filter(NewsItem.publish_date <= query_params.end_date)

        # 最低质量分筛选
        if query_params.min_quality_score:
            query = query.filter(NewsItem.quality_score >= query_params.min_quality_score)

        # 排序
        sort_column = getattr(NewsItem, query_params.sort_by, NewsItem.publish_date)
        if query_params.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        total = query.count()
        items = query.offset((query_params.page - 1) * query_params.page_size).limit(query_params.page_size).all()

        return items, total

    def get_news_detail(self, db: Session, news_id: str, increment_view: bool = True) -> Optional[NewsItem]:
        """获取资讯详情"""
        news = db.query(NewsItem).filter(
            NewsItem.id == news_id,
            NewsItem.is_deleted == False,
        ).first()

        if not news:
            raise BusinessException(code=404, message="资讯不存在")

        # 增加浏览量
        if increment_view:
            news.view_count += 1
            db.commit()

        return news

    def get_stats(self, db: Session) -> NewsStatsSchema:
        """获取统计数据"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 今日新增
        today_new = db.query(func.count(NewsItem.id)).filter(
            NewsItem.publish_date == today,
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        ).scalar() or 0

        # 昨日新增（用于环比）
        yesterday_new = db.query(func.count(NewsItem.id)).filter(
            NewsItem.publish_date == yesterday,
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        ).scalar() or 0

        # 环比变化率
        today_new_trend = 0.0
        if yesterday_new > 0:
            today_new_trend = round((today_new - yesterday_new) / yesterday_new * 100, 1)

        # 招投标数量
        bidding_count = db.query(func.count(NewsItem.id)).filter(
            NewsItem.info_type == "bidding",
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        ).scalar() or 0

        # 政策动态数量
        policy_count = db.query(func.count(NewsItem.id)).filter(
            NewsItem.info_type == "policy",
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        ).scalar() or 0

        # 企业动态数量
        enterprise_count = db.query(func.count(NewsItem.id)).filter(
            NewsItem.info_type == "enterprise",
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        ).scalar() or 0

        # 高价值商机数量（质量分>=80）
        high_value_count = db.query(func.count(NewsItem.id)).filter(
            NewsItem.quality_score >= 80,
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        ).scalar() or 0

        return NewsStatsSchema(
            today_new=today_new,
            bidding_count=bidding_count,
            policy_count=policy_count,
            enterprise_count=enterprise_count,
            high_value_count=high_value_count,
            today_new_trend=today_new_trend,
        )

    def audit_news(
        self, db: Session, news_id: str, status: str, comment: str = "", reviewer_id: str = None
    ) -> NewsItem:
        """审核资讯"""
        news = self.get(db, news_id)
        if not news:
            raise BusinessException(code=404, message="资讯不存在")

        if status not in ["published", "rejected"]:
            raise BusinessException(code=400, message="无效的审核状态")

        news.status = status
        news.reviewer_id = reviewer_id
        news.reviewed_at = datetime.utcnow()
        news.review_comment = comment

        db.commit()
        db.refresh(news)
        return news

    def increment_lead_count(self, db: Session, news_id: str):
        """增加线索计数"""
        news = self.get(db, news_id)
        if news:
            news.lead_count += 1
            db.commit()


class TagService(CRUDBase[TagDictionary, TagSchema, TagSchema]):
    """标签服务"""

    def __init__(self):
        super().__init__(TagDictionary)

    def get_tags_by_type(self, db: Session, tag_type: str) -> List[TagDictionary]:
        """按类型获取标签"""
        return db.query(TagDictionary).filter(
            TagDictionary.tag_type == tag_type,
            TagDictionary.is_active == True,
        ).order_by(TagDictionary.sort_order).all()

    def get_all_tags(self, db: Session) -> dict:
        """获取所有标签（按类型分组）"""
        tags = db.query(TagDictionary).filter(
            TagDictionary.is_active == True
        ).order_by(TagDictionary.tag_type, TagDictionary.sort_order).all()

        result = {}
        for tag in tags:
            if tag.tag_type not in result:
                result[tag.tag_type] = []
            result[tag.tag_type].append({
                "code": tag.tag_code,
                "name": tag.tag_name,
                "color": tag.tag_color,
            })
        return result


class TopicService(CRUDBase[Topic, dict, dict]):
    """专题服务"""

    def __init__(self):
        super().__init__(Topic)

    def get_active_topics(self, db: Session) -> List[Topic]:
        """获取活跃专题"""
        topics = db.query(Topic).filter(
            Topic.is_active == True
        ).order_by(Topic.sort_order).all()

        # 补充统计数据
        for topic in topics:
            topic.total_count = self._get_topic_news_count(db, topic)
            topic.month_new_count = self._get_topic_month_new_count(db, topic)
            topic.high_value_count = self._get_topic_high_value_count(db, topic)

        return topics

    def _get_topic_news_count(self, db: Session, topic: Topic) -> int:
        """获取专题下资讯总数"""
        query = db.query(NewsItem).filter(
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        )
        query = self._apply_topic_filter(query, topic)
        return query.count()

    def _get_topic_month_new_count(self, db: Session, topic: Topic) -> int:
        """获取专题本月新增数"""
        first_day_of_month = date.today().replace(day=1)
        query = db.query(NewsItem).filter(
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
            NewsItem.publish_date >= first_day_of_month,
        )
        query = self._apply_topic_filter(query, topic)
        return query.count()

    def _get_topic_high_value_count(self, db: Session, topic: Topic) -> int:
        """获取专题高价值资讯数"""
        query = db.query(NewsItem).filter(
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
            NewsItem.quality_score >= 80,
        )
        query = self._apply_topic_filter(query, topic)
        return query.count()

    def _apply_topic_filter(self, query, topic: Topic):
        """应用专题筛选条件（兼容SQLite）"""
        config = topic.filter_config or {}
        # info_type用IN查询（兼容所有数据库）
        if config.get("info_type"):
            info_types = config["info_type"]
            if isinstance(info_types, list):
                query = query.filter(NewsItem.info_type.in_(info_types))
            else:
                query = query.filter(NewsItem.info_type == info_types)
        # business_category用IN查询（兼容所有数据库）
        if config.get("business_category"):
            biz_cats = config["business_category"]
            if isinstance(biz_cats, list):
                query = query.filter(NewsItem.business_category.in_(biz_cats))
            else:
                query = query.filter(NewsItem.business_category == biz_cats)
        # industry_tags和area_tags的JSON包含查询在SQLite下不兼容
        # 这里先跳过，后续可以在Python层过滤
        return query

    def get_topic_news(
        self, db: Session, topic_id: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[NewsItem], int]:
        """获取专题下的资讯列表"""
        topic = self.get(db, topic_id)
        if not topic:
            raise BusinessException(code=404, message="专题不存在")

        query = db.query(NewsItem).filter(
            NewsItem.status == "published",
            NewsItem.is_deleted == False,
        )
        query = self._apply_topic_filter(query, topic)
        query = query.order_by(desc(NewsItem.publish_date))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total


# 服务单例
news_service = NewsService()
tag_service = TagService()
topic_service = TopicService()

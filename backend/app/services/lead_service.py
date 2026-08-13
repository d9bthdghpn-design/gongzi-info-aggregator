"""
线索服务 - 线索全生命周期管理
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session

from app.models import Lead, LeadFollowup, User
from app.schemas.lead import (
    LeadCreateSchema, LeadUpdateSchema, LeadQuerySchema,
    LeadFollowupCreateSchema, LeadAssignSchema,
)
from app.services.base import CRUDBase
from app.core.exceptions import BusinessException
from app.services.news_service import news_service

# 允许排序的字段白名单
_LEAD_SORT_COLUMNS = {
    "created_at": Lead.created_at,
    "updated_at": Lead.updated_at,
    "priority": Lead.priority,
    "status": Lead.status,
    "protect_expire_at": Lead.protect_expire_at,
    "next_followup_time": Lead.next_followup_time,
}


class LeadService(CRUDBase[Lead, LeadCreateSchema, LeadUpdateSchema]):
    """线索服务"""

    def __init__(self):
        super().__init__(Lead)

    def get_lead_list(
        self, db: Session, query_params: LeadQuerySchema, current_user: User = None
    ) -> Tuple[List[Lead], int]:
        """获取线索列表"""
        query = db.query(Lead).filter(Lead.is_deleted == False)

        # 关键词搜索
        if query_params.keyword:
            keyword = f"%{query_params.keyword}%"
            query = query.filter(
                or_(
                    Lead.company_name.ilike(keyword),
                    Lead.contact_person.ilike(keyword),
                    Lead.project_desc.ilike(keyword),
                )
            )

        # 行业筛选
        if query_params.industry:
            query = query.filter(Lead.industry == query_params.industry)

        # 区域筛选
        if query_params.area:
            query = query.filter(Lead.area == query_params.area)

        # 状态筛选
        if query_params.status:
            query = query.filter(Lead.status == query_params.status)

        # 优先级筛选
        if query_params.priority:
            query = query.filter(Lead.priority == query_params.priority)

        # 公海池筛选
        if query_params.public_pool is not None:
            query = query.filter(Lead.public_pool == query_params.public_pool)

        # 负责人筛选
        if query_params.assignee_id:
            query = query.filter(Lead.assignee_id == query_params.assignee_id)

        # 排序
        sort_column = _LEAD_SORT_COLUMNS.get(query_params.sort_by, Lead.created_at)
        if query_params.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        total = query.count()
        items = query.offset((query_params.page - 1) * query_params.page_size).limit(query_params.page_size).all()

        return items, total

    def create_lead(self, db: Session, obj_in: LeadCreateSchema, reporter_id: str) -> Lead:
        """创建线索"""
        lead_data = obj_in.model_dump()
        lead_data["reporter_id"] = reporter_id
        lead_data["status"] = "new"

        lead = Lead(**lead_data)
        db.add(lead)
        db.commit()
        db.refresh(lead)

        # 如果有关联资讯，增加线索计数
        if obj_in.source_news_id:
            news_service.increment_lead_count(db, obj_in.source_news_id)

        return lead

    def get_my_leads(self, db: Session, user_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[Lead], int]:
        """获取我的线索"""
        query = db.query(Lead).filter(
            Lead.assignee_id == user_id,
            Lead.is_deleted == False,
            Lead.public_pool == False,
        ).order_by(desc(Lead.created_at))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_public_pool_leads(
        self, db: Session, page: int = 1, page_size: int = 20, keyword: str = None
    ) -> Tuple[List[Lead], int]:
        """获取公海池线索"""
        query = db.query(Lead).filter(
            Lead.public_pool == True,
            Lead.is_deleted == False,
        )

        if keyword:
            keyword = f"%{keyword}%"
            query = query.filter(Lead.company_name.ilike(keyword))

        query = query.order_by(desc(Lead.created_at))
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def claim_lead(self, db: Session, lead_id: str, user_id: str, protect_days: int = 30) -> Lead:
        """领取公海线索"""
        lead = self.get(db, lead_id)
        if not lead:
            raise BusinessException(code=404, message="线索不存在")

        if not lead.public_pool:
            raise BusinessException(code=400, message="线索不在公海池中")

        lead.public_pool = False
        lead.assignee_id = user_id
        lead.status = "active"
        lead.protect_expire_at = datetime.now(timezone.utc) + timedelta(days=protect_days)

        db.commit()
        db.refresh(lead)
        return lead

    def release_lead(self, db: Session, lead_id: str, user_id: str) -> Lead:
        """释放线索到公海"""
        lead = self.get(db, lead_id)
        if not lead:
            raise BusinessException(code=404, message="线索不存在")

        if str(lead.assignee_id) != str(user_id):
            raise BusinessException(code=403, message="无权释放他人的线索")

        lead.public_pool = True
        lead.assignee_id = None
        lead.status = "released"

        db.commit()
        db.refresh(lead)
        return lead

    def assign_lead(self, db: Session, lead_id: str, assign_data: LeadAssignSchema) -> Lead:
        """分配线索"""
        lead = self.get(db, lead_id)
        if not lead:
            raise BusinessException(code=404, message="线索不存在")

        lead.assignee_id = assign_data.assignee_id
        lead.public_pool = False
        lead.status = "active"
        lead.protect_expire_at = datetime.now(timezone.utc) + timedelta(days=assign_data.protect_days)

        db.commit()
        db.refresh(lead)
        return lead


class LeadFollowupService:
    """线索跟进服务"""

    def get_followups(self, db: Session, lead_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[LeadFollowup], int]:
        """获取线索跟进记录"""
        query = db.query(LeadFollowup).filter(
            LeadFollowup.lead_id == lead_id
        ).order_by(desc(LeadFollowup.followup_time))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def add_followup(
        self, db: Session, lead_id: str, obj_in: LeadFollowupCreateSchema, follower_id: str
    ) -> LeadFollowup:
        """添加跟进记录"""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise BusinessException(code=404, message="线索不存在")

        followup_data = obj_in.model_dump()
        followup_data["lead_id"] = lead_id
        followup_data["follower_id"] = follower_id

        followup = LeadFollowup(**followup_data)
        db.add(followup)

        # 更新线索的最后跟进时间和下次跟进时间
        lead.last_followup_time = datetime.now(timezone.utc)
        if obj_in.next_time:
            lead.next_followup_time = obj_in.next_time

        # 续期保护期（每次跟进续期7天）
        if lead.protect_expire_at:
            lead.protect_expire_at = lead.protect_expire_at + timedelta(days=7)

        db.commit()
        db.refresh(followup)
        return followup


# 服务单例
lead_service = LeadService()
lead_followup_service = LeadFollowupService()

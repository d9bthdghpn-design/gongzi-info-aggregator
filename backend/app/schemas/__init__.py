"""
Schema统一导出
"""
from app.schemas.base import ResponseBase, PageResponse, DataResponse, ListResponse, BaseSchema
from app.schemas.news import (
    NewsItemSchema, NewsItemDetailSchema, NewsItemAdminSchema,
    NewsItemCreateSchema, NewsItemUpdateSchema, NewsQuerySchema,
    NewsStatsSchema, TagSchema, TopicSchema,
)
from app.schemas.lead import (
    LeadSchema, LeadCreateSchema, LeadUpdateSchema, LeadQuerySchema,
    LeadFollowupSchema, LeadFollowupCreateSchema, LeadAssignSchema,
)
from app.schemas.user import (
    UserSchema, UserCreateSchema, UserUpdateSchema,
    LoginSchema, TokenSchema, RefreshTokenSchema,
)
from app.schemas.briefing import DailyBriefingSchema, BriefingGenerateSchema

__all__ = [
    "ResponseBase", "PageResponse", "DataResponse", "ListResponse", "BaseSchema",
    # News
    "NewsItemSchema", "NewsItemDetailSchema", "NewsItemAdminSchema",
    "NewsItemCreateSchema", "NewsItemUpdateSchema", "NewsQuerySchema",
    "NewsStatsSchema", "TagSchema", "TopicSchema",
    # Lead
    "LeadSchema", "LeadCreateSchema", "LeadUpdateSchema", "LeadQuerySchema",
    "LeadFollowupSchema", "LeadFollowupCreateSchema", "LeadAssignSchema",
    # User
    "UserSchema", "UserCreateSchema", "UserUpdateSchema",
    "LoginSchema", "TokenSchema", "RefreshTokenSchema",
    # Briefing
    "DailyBriefingSchema", "BriefingGenerateSchema",
]

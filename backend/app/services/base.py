"""
基础服务类
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """CRUD基础服务类"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """根据ID获取"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, page: int = 1, page_size: int = 20, filters: dict = None
    ) -> tuple[List[ModelType], int]:
        """分页查询"""
        query = db.query(self.model)
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """创建"""
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """更新"""
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> ModelType:
        """删除"""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

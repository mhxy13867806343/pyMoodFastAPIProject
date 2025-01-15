from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
import time

from config.api_descriptions import ApiDescriptions
from config.error_messages import SYSTEM_ERROR, USER_ERROR
from models.dicts.model import SYSDict, SYSDictItem
from app.dicts.schemas import (
    DictCreate, DictUpdate, DictResponse, DictListResponse,
    DictItemCreate, DictItemUpdate, DictItemResponse,
    DictQuery, DictItemQuery
)
from tool.db import getDbSession
from tool.getLogger import globalLogger
from tool.msg import Message

dictApp = APIRouter(tags=["字典管理"])

@dictApp.get(
    "/dict/list",
    summary="获取字典列表",
    response_model=DictListResponse
)
async def get_dict_list(
    query: DictQuery = Depends(),
    db: Session = Depends(getDbSession)
):
    """获取字典列表"""
    try:
        query_obj = db.query(SYSDict)
        if query.type:
            query_obj = query_obj.filter(SYSDict.type == query.type)
        
        total = query_obj.count()
        items = query_obj.offset((query.page - 1) * query.page_size).limit(query.page_size).all()
        
        return Message.success(data={"total": total, "items": items})
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.get(
    "/dict/{code}",
    summary="获取字典详情",
    response_model=DictResponse
)
async def get_dict_detail(
    code: str,
    db: Session = Depends(getDbSession)
):
    """获取字典详情"""
    try:
        dict_item = db.query(SYSDict).filter(SYSDict.code == code).first()
        if not dict_item:
            return Message.error(message="字典不存在")
        
        return Message.success(data=dict_item)
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.post(
    "/dict",
    summary="创建字典"
)
async def create_dict(
    request: DictCreate,
    db: Session = Depends(getDbSession)
):
    """创建字典"""
    try:
        # 检查key是否已存在
        if db.query(SYSDict).filter(SYSDict.key == request.key).first():
            return Message.error(message="字典key已存在")
        
        # 生成唯一code
        code = f"DICT_{str(uuid.uuid4()).replace('-', '')}"
        
        dict_item = SYSDict(
            code=code,
            name=request.name,
            key=request.key,
            value=request.value,
            type=request.type,
            status=0  # 默认正常状态
        )
        
        db.add(dict_item)
        db.commit()
        db.refresh(dict_item)
        
        return Message.success(data=dict_item)
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.put(
    "/dict/{code}",
    summary="更新字典"
)
async def update_dict(
    code: str,
    request: DictUpdate,
    db: Session = Depends(getDbSession)
):
    """更新字典"""
    try:
        dict_item = db.query(SYSDict).filter(SYSDict.code == code).first()
        if not dict_item:
            return Message.error(message="字典不存在")
        
        # 检查key是否已存在（排除自身）
        if db.query(SYSDict).filter(
            SYSDict.key == request.key,
            SYSDict.code != code
        ).first():
            return Message.error(message="字典key已存在")
        
        # 更新字段
        dict_item.name = request.name
        dict_item.key = request.key
        dict_item.value = request.value
        dict_item.type = request.type
        
        db.commit()
        db.refresh(dict_item)
        
        return Message.success(data=dict_item)
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.delete(
    "/dict/{code}",
    summary="删除字典"
)
async def delete_dict(
    code: str,
    db: Session = Depends(getDbSession)
):
    """删除字典"""
    try:
        dict_item = db.query(SYSDict).filter(SYSDict.code == code).first()
        if not dict_item:
            return Message.error(message="字典不存在")
        
        # 删除关联的字典项
        db.query(SYSDictItem).filter(SYSDictItem.dict_id == dict_item.id).delete()
        
        # 删除字典
        db.delete(dict_item)
        db.commit()
        
        return Message.success(data=None)
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

# 字典项接口
@dictApp.get(
    "/dict/items/{dict_code}",
    summary="获取字典项列表",
    response_model=DictItemResponse
)
async def get_dict_items(
    dict_code: str,
    query: DictItemQuery = Depends(),
    db: Session = Depends(getDbSession)
):
    """获取字典项列表"""
    try:
        # 获取字典
        dict_item = db.query(SYSDict).filter(SYSDict.code == dict_code).first()
        if not dict_item:
            return Message.error(message="字典不存在")
        
        # 查询字典项
        query_obj = db.query(SYSDictItem).filter(SYSDictItem.dict_id == dict_item.id)
        
        total = query_obj.count()
        items = query_obj.offset((query.page - 1) * query.page_size).limit(query.page_size).all()
        
        return Message.success(data={"total": total, "items": items})
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.post(
    "/dict/item",
    summary="创建字典项"
)
async def create_dict_item(
    request: DictItemCreate,
    db: Session = Depends(getDbSession)
):
    """创建字典项"""
    try:
        # 检查字典是否存在
        dict_item = db.query(SYSDict).filter(SYSDict.id == request.dict_id).first()
        if not dict_item:
            return Message.error(message="字典不存在")
        
        # 检查key是否已存在
        if db.query(SYSDictItem).filter(
            SYSDictItem.dict_id == request.dict_id,
            SYSDictItem.key == request.key
        ).first():
            return Message.error(message="字典项key已存在")
        
        # 生成唯一code
        item_code = f"DICTITEM_{str(uuid.uuid4()).replace('-', '')}"
        
        dict_item = SYSDictItem(
            item_code=item_code,
            dict_id=request.dict_id,
            name=request.name,
            key=request.key,
            value=request.value,
            type=request.type,
            status=0  # 默认正常状态
        )
        
        db.add(dict_item)
        db.commit()
        db.refresh(dict_item)
        
        return Message.success(data=dict_item)
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.put(
    "/dict/item/{code}",
    summary="更新字典项"
)
async def update_dict_item(
    code: str,
    request: DictItemUpdate,
    db: Session = Depends(getDbSession)
):
    """更新字典项"""
    try:
        dict_item = db.query(SYSDictItem).filter(SYSDictItem.item_code == code).first()
        if not dict_item:
            return Message.error(message="字典项不存在")
        
        # 检查key是否已存在（排除自身）
        if db.query(SYSDictItem).filter(
            SYSDictItem.dict_id == request.dict_id,
            SYSDictItem.key == request.key,
            SYSDictItem.item_code != code
        ).first():
            return Message.error(message="字典项key已存在")
        
        # 更新字段
        dict_item.name = request.name
        dict_item.key = request.key
        dict_item.value = request.value
        dict_item.type = request.type
        
        db.commit()
        db.refresh(dict_item)
        
        return Message.success(data=dict_item)
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.delete(
    "/dict/item/{code}",
    summary="删除字典项"
)
async def delete_dict_item(
    code: str,
    db: Session = Depends(getDbSession)
):
    """删除字典项"""
    try:
        dict_item = db.query(SYSDictItem).filter(SYSDictItem.item_code == code).first()
        if not dict_item:
            return Message.error(message="字典项不存在")
        
        db.delete(dict_item)
        db.commit()
        
        return Message.success(data=None)
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])
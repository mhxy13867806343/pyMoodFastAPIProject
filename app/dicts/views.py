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

dictApp = APIRouter(tags=[ApiDescriptions.DICT_TAGS])

@dictApp.get(
    "/list",
    summary=ApiDescriptions.DICT_GET_DESC["summary"],
    description=ApiDescriptions.DICT_GET_DESC["description"]
)
async def get_dict_list(
    query: DictQuery = Depends(),
    db: Session = Depends(getDbSession)
):
    """获取字典列表"""
    try:
        query_obj = db.query(SYSDict)
        
        # 构建查询条件
        conditions = []
        if query.key:
            conditions.append(SYSDict.key == query.key)
        if query.name:
            conditions.append(SYSDict.name == query.name)
        if query.type:
            conditions.append(SYSDict.type == query.type)
        if query.status:
            conditions.append(SYSDict.status == query.status)
            
        # 如果有查询条件，添加到查询对象中
        if conditions:
            query_obj = query_obj.filter(*conditions)
        
        total = query_obj.count()
        items = query_obj.offset((query.page - 1) * query.page_size).limit(query.page_size).all()
        
        return Message.success(data={
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "data": [item.to_dict() for item in items]  # 确保返回的是可序列化的字典
        })
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.get(
    "/{code}",
    summary=ApiDescriptions.DICT_CODE_DESC["summary"],
    description=ApiDescriptions.DICT_CODE_DESC["description"]
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
        
        return Message.success(data=dict_item.to_dict()) # 修改此处
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.post(
    "/add",
    summary=ApiDescriptions.DICT_POST_DESC["summary"],
    description=ApiDescriptions.DICT_POST_DESC["description"]
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
        if not request.name:
            return Message.error(message="字典名称不能为空")
        if not request.value:
            return Message.error(message="字典value不能为空")
        # 生成唯一code
        code = f"DICT_{str(uuid.uuid4()).replace('-', '')}"
        
        dict_item = SYSDict(
            code=code,
            name=request.name,
            key=request.key,
            value=request.value,
            type=request.type or 0,
            status=0  # 默认正常状态
        )
        
        db.add(dict_item)
        db.commit()
        db.refresh(dict_item)
        
        return Message.success(data=dict_item.to_dict()) # 修改此处
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.put(
    "/{code}",
    summary=ApiDescriptions.DICT_PUT_DESC["summary"],
    description=ApiDescriptions.DICT_PUT_DESC["description"]
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
        
        return Message.success(data=dict_item.to_dict()) # 修改此处
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.delete(
    "/dict/{code}",
    summary=ApiDescriptions.DICT_DEL_DESC["summary"],
    description=ApiDescriptions.DICT_DEL_DESC["description"]
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
    summary=ApiDescriptions.DICT_ITEMS_GET_DESC["summary"],
    description=ApiDescriptions.DICT_ITEMS_GET_DESC["description"]
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
        
        return Message.success(data={"total": total, "items": [item.to_dict() for item in items]}) # 修改此处
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.post(
    "/dict/item",
    summary=ApiDescriptions.DICT_ITEM_POST_DESC["summary"],
    description=ApiDescriptions.DICT_ITEM_POST_DESC["description"]
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
        
        return Message.success(data=dict_item.to_dict()) # 修改此处
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.put(
    "/dict/item/{code}",
    summary=ApiDescriptions.DICT_ITEM_PUT_DESC["summary"],
    description=ApiDescriptions.DICT_ITEM_PUT_DESC["description"]
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
        
        return Message.success(data=dict_item.to_dict()) # 修改此处
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"])
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"])

@dictApp.delete(
    "/dict/item/{code}",
    summary=ApiDescriptions.DICT_ITEM_DEL_DESC["summary"],
    description=ApiDescriptions.DICT_ITEM_DEL_DESC["description"]
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
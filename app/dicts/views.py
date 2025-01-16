import string
from random import random
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
import time

from config.api_descriptions import ApiDescriptions
from config.error_code import ErrorCode
from config.error_messages import SYSTEM_ERROR, USER_ERROR
from models.dicts.model import SYSDict, SYSDictItem
from tool.dbEnum import DictStatus
from app.dicts.schemas import (
    DictBaseCode,
    DictBaseListMore, DictCreate, DictBaseModelCode
)
from tool.db import getDbSession
from tool.dbTools import sysHex4randCode, get_pagination, get_total_count
from tool.getLogger import globalLogger
from tool.msg import Message

dictApp = APIRouter(tags=[ApiDescriptions.DICT_TAGS])

@dictApp.get(
    "/list",
    summary=ApiDescriptions.DICT_GET_DESC["summary"],
    description=ApiDescriptions.DICT_GET_DESC["description"]
)
async def get_dict_list(
    query: DictBaseListMore = Depends(),
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
        if query.status is not None:  # 如果status有值（包括0），则添加条件
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
            "data": [item.to_dict() for item in items]
        })
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"], code=ErrorCode.DATABASE_ERROR)

@dictApp.get(
    "/{code}",
    summary=ApiDescriptions.DICT_GET_DESC["summary"],
    description=ApiDescriptions.DICT_GET_DESC["description"]
)
async def get_dict_by_id(
    code:str,
    db: Session = Depends(getDbSession)
):
    """获取单个字典"""
    try:
        dict_item = db.query(SYSDict).filter(
            SYSDict.code ==code
        ).first()
        
        if not dict_item:
            return Message.error(message="字典不存在或已禁用",code=ErrorCode.BAD_REQUEST)
        
        return Message.success(data=dict_item.to_dict())
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.SYSTEM_ERROR)

@dictApp.post('/add',
              summary=ApiDescriptions.DICT_ITEM_POST_DESC["summary"],
              description=ApiDescriptions.DICT_ITEM_POST_DESC["description"]
              )
async def add_dict(
    request: DictCreate,
    db: Session = Depends(getDbSession)
):
    """添加字典"""
    try:
        if not request.name:
            return Message.error(message="name不能为空", code=ErrorCode.BAD_REQUEST)
        if not request.key:
            return Message.error(message="key不能为空", code=ErrorCode.BAD_REQUEST)
        if not request.value:
            return Message.error(message="value不能为空", code=ErrorCode.BAD_REQUEST)
        if not request.type:
            return Message.error(message="type不能为空", code=ErrorCode.BAD_REQUEST)
            
        # 检查key或name是否已存在
        dict_item = db.query(SYSDict).filter(
            or_(
                SYSDict.key == request.key,
                SYSDict.name == request.name
            )
        ).first()
        if dict_item:
            if dict_item.key == request.key:
                return Message.error(message="字典key已存在", code=ErrorCode.BAD_REQUEST)
            return Message.error(message="字典name已存在", code=ErrorCode.BAD_REQUEST)
        code =sysHex4randCode()
        dict_item = SYSDict(
            code=code,
            name=request.name,
            key=request.key,
            value=request.value,
            type=request.type,
            status=0
        )
        db.add(dict_item)
        db.commit()
        return Message.success(data=dict_item.to_dict())
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"], code=ErrorCode.BAD_REQUEST)
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.BAD_REQUEST)
@dictApp.put(
    "/update",
    summary=ApiDescriptions.DICT_PUT_DESC["summary"],
    description=ApiDescriptions.DICT_PUT_DESC["description"]
)
async def update_dict(
    request: DictBaseCode,
    db: Session = Depends(getDbSession)
):
    """更新字典"""
    try:
        if not request.name or not request.key or not request.value:
            return Message.error(message="name, key, value不能为空", code=ErrorCode.BAD_REQUEST)

        dict_item = db.query(SYSDict).filter(SYSDict.code == request.code).first()
        if not dict_item:
            return Message.error(message="字典不存在", code=ErrorCode.BAD_REQUEST)
            
        # 如果字典已禁用，不允许修改
        if dict_item.status == DictStatus.DISABLED.value:
            return Message.error(message="禁用状态的字典不允许修改", code=ErrorCode.BAD_REQUEST)

        # 检查name和key是否与其他记录冲突
        existing = db.query(SYSDict).filter(
            (SYSDict.name == request.name) | (SYSDict.key == request.key),
            SYSDict.code != request.code
        ).first()
        
        if existing:
            if existing.name == request.name:
                return Message.error(message=f"name:{request.name}已存在, 请更换名称", code=ErrorCode.BAD_REQUEST)
            else:
                return Message.error(message=f"key:{request.key}已存在, 请更换key", code=ErrorCode.BAD_REQUEST)

        # 更新字段
        dict_item.name = request.name
        dict_item.key = request.key
        dict_item.value = request.value
        dict_item.type = request.type
        dict_item.status=request.status
        
        db.commit()
        db.refresh(dict_item)
        
        return Message.success(data=dict_item.to_dict())
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"], code=ErrorCode.DATABASE_ERROR)
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.SYSTEM_ERROR)

@dictApp.put(
    "/status",
    summary=ApiDescriptions.DICT_STATUS_PUT_DESC["summary"],
    description=ApiDescriptions.DICT_STATUS_PUT_DESC["description"]
)
async def update_dict_status(
        request: DictBaseModelCode,
    db: Session = Depends(getDbSession)
):
    """更新字典状态"""
    try:
        if request.status not in [DictStatus.NORMAL.value, DictStatus.DISABLED.value]:
            return Message.error(message="无效的状态值",code=ErrorCode.BAD_REQUEST)

        dict_item = db.query(SYSDict).filter(SYSDict.code == request.code).first()
        if not dict_item:
            return Message.error(message="字典不存在",code=ErrorCode.BAD_REQUEST)
        if dict_item.status == request.status:
            return Message.error(message=f"当前字典状态未改变,无需更改",code=ErrorCode.BAD_REQUEST)
        dict_item.status = request.status
        db.commit()
        db.refresh(dict_item)
        
        status_text = "启用" if request.status == DictStatus.NORMAL.value else "禁用"
        return Message.success(data=dict_item.to_dict(), message=f"字典{status_text}成功")
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"], code=ErrorCode.DATABASE_ERROR)
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.SYSTEM_ERROR)

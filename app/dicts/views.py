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
    DictBaseListMore, DictCreate, DictBaseModelCode, DictBaseModelItem
)
from tool.db import getDbSession
from tool.dbTools import sysHex4randCode, get_pagination
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
        kwargs = {}
        
        # status: 只有 0 和 1 才过滤，其他值都查询所有
        if query.status in [0, 1]:
            kwargs['status'] = query.status
            
        # 其他字段：空字符串查询所有，有值才过滤
        if query.type is not None and query.type != "":
            kwargs['type'] = query.type
        if query.key is not None and query.key != "":
            kwargs['key'] = query.key
        if query.name is not None and query.name != "":
            kwargs['name'] = query.name
        if query.value is not None and query.value != "":
            kwargs['value'] = query.value
            
        print("Query parameters:", kwargs)  # 调试日志
        
        pagination = get_pagination(
            model=SYSDict,
            session=db,
            pageNum=query.page,
            pageSize=query.page_size,
            **kwargs
        )
        return Message.success(data=pagination)
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
@dictApp.post(
    "/item/add",
    summary=ApiDescriptions.DICT_STATUS_PUT_DESC["summary"],
    description=ApiDescriptions.DICT_STATUS_PUT_DESC["description"]
)
async def add_item_data(
        request: DictBaseModelItem,
    db: Session = Depends(getDbSession)
):
    try:
        if not  request.code:
            return Message.error(message="父字典必要参数不能为空",code=ErrorCode.BAD_REQUEST)
        if not request.name:
            return Message.error(message="字典名称不能为空",code=ErrorCode.BAD_REQUEST)
        if not request.key:
            return Message.error(message="字典key不能为空",code=ErrorCode.BAD_REQUEST)
        if not request.value:
            return Message.error(message="字典value不能为空",code=ErrorCode.BAD_REQUEST)
        dict_item = SYSDictItem(
            dict_id=request.dict_id,
            name=request.name,
            key=request.key,
            value=request.value,
            type=request.type,
            status=0
        )
        db.add(dict_item)
        db.commit()
        return Message.success(data=dict_item.to_dict(), message="添加字典成功")
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.SYSTEM_ERROR)
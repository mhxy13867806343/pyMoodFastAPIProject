@dictApp.post(
    "/items/add",
    summary=ApiDescriptions.DICT_ITEM_POST_DESC["summary"],
    description=ApiDescriptions.DICT_ITEM_POST_DESC["description"]
)
async def create_dict_item(
        request: DictItemUpdate,
        db: Session = Depends(getDbSession)
):
    """创建字典项"""
    try:
        if not request.name:
            return Message.error(message="字典项名称不能为空", code=ErrorCode.BAD_REQUEST)
        if not request.key:
            return Message.error(message="字典项key不能为空", code=ErrorCode.BAD_REQUEST)
        if not request.value:
            return Message.error(message="字典项value不能为空", code=ErrorCode.BAD_REQUEST)

        # 检查字典是否存在且状态正常
        dict_obj = db.query(SYSDict).filter(
            SYSDict.id == request.dict_id,
            SYSDict.status == DictStatus.NORMAL.value
        ).first()

        if not dict_obj:
            return Message.error(message="字典不存在或已禁用", code=ErrorCode.BAD_REQUEST)

        # 检查name和key是否已存在
        existing = db.query(SYSDictItem).filter(
            SYSDictItem.dict_id == dict_obj.id,
            (SYSDictItem.name == request.name) | (SYSDictItem.key == request.key)
        ).first()

        if existing:
            if existing.name == request.name:
                return Message.error(message="字典项名称已存在", code=ErrorCode.BAD_REQUEST)
            else:
                return Message.error(message="字典项key已存在", code=ErrorCode.BAD_REQUEST)

        # 生成唯一的code
        item_code = f"DICTITEM_{uuid.uuid4().hex}"

        dict_item = SYSDictItem(
            item_code=item_code,
            dict_id=dict_obj.id,
            name=request.name,
            key=request.key,
            value=request.value,
            type=request.type,
            status=DictStatus.NORMAL.value,
            create_time=int(time.time()),
            last_time=int(time.time())
        )

        db.add(dict_item)
        db.commit()
        db.refresh(dict_item)

        return Message.success(data=dict_item.to_dict())
    except SQLAlchemyError as e:
        print(333, e)
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"], code=ErrorCode.BAD_REQUEST)
    except Exception as e:
        print(333, e)
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.SYSTEM_ERROR)


@dictApp.get(
    "/items/{code}",
    summary=ApiDescriptions.DICT_ITEMS_GET_DESC["summary"],
    description=ApiDescriptions.DICT_ITEMS_GET_DESC["description"]
)
async def get_dict_items(
        code: str,
        query: DictItemQuery = Depends(),
        db: Session = Depends(getDbSession)
):
    """获取字典项列表"""
    try:
        # 获取字典
        dict_obj = db.query(SYSDict).filter(
            SYSDict.code == code,
            SYSDict.status == DictStatus.NORMAL.value
        ).first()
        if not dict_obj:
            return Message.error(message="字典不存在或已禁用", code=ErrorCode.BAD_REQUEST)

        # 查询字典项
        query_obj = db.query(SYSDictItem).filter(SYSDictItem.dict_id == dict_obj.id)

        # 构建查询条件
        conditions = []
        if query.key:
            conditions.append(SYSDictItem.key == query.key)
        if query.name:
            conditions.append(SYSDictItem.name == query.name)
        if query.type:
            conditions.append(SYSDictItem.type == query.type)
        if query.status is not None:
            conditions.append(SYSDictItem.status == query.status)
        else:
            # 默认只显示正常状态的字典项
            conditions.append(SYSDictItem.status == DictStatus.NORMAL.value)

        if conditions:
            query_obj = query_obj.filter(*conditions)

        total = query_obj.count()
        items = query_obj.offset((query.page - 1) * query.page_size).limit(query.page_size).all()

        return Message.success(data={
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "items": [item.to_dict() for item in items]
        })
    except Exception as e:
        print(33333, e)
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.SYSTEM_ERROR)


@dictApp.put(
    "/item/edit",
    summary=ApiDescriptions.DICT_ITEM_PUT_DESC["summary"],
    description=ApiDescriptions.DICT_ITEM_PUT_DESC["description"]
)
async def update_dict_item(
        request: DictItemUpdate,
        db: Session = Depends(getDbSession)
):
    """更新字典项"""
    try:
        # 检查字典是否存在且状态正常
        dict_obj = db.query(SYSDict).filter(
            SYSDict.code == request.code,
            SYSDict.status == DictStatus.NORMAL.value
        ).first()
        if not dict_obj:
            return Message.error(message="字典不存在或已禁用", code=ErrorCode.BAD_REQUEST)

        # 检查字典项是否存在且属于该字典
        dict_item = db.query(SYSDictItem).filter(
            SYSDictItem.item_code == request.code,
            SYSDictItem.dict_id == dict_obj.id
        ).first()
        if not dict_item:
            return Message.error(message="字典项不存在", code=ErrorCode.BAD_REQUEST)

        # 如果字典项已禁用，不允许修改
        if dict_item.status == DictStatus.DISABLED.value:
            return Message.error(message="禁用状态的字典项不允许修改", code=ErrorCode.BAD_REQUEST)

        # 检查name和key是否与其他记录冲突
        conditions = []
        if request.name != dict_item.name:
            conditions.append(SYSDictItem.name == request.name)
        if request.key != dict_item.key:
            conditions.append(SYSDictItem.key == request.key)

        if conditions:
            existing = db.query(SYSDictItem).filter(
                SYSDictItem.dict_id == dict_obj.id,
                or_(*conditions),
                SYSDictItem.item_code != request.code
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
    "/items/status/{dict_id}",
    summary="更新字典项状态",
    description="启用或禁用字典项"
)
async def update_dict_item_status(
        dict_id: int,
        item_code: str,
        status: int,
        db: Session = Depends(getDbSession)
):
    """更新字典项状态"""
    try:
        if status not in [DictStatus.NORMAL.value, DictStatus.DISABLED.value]:
            return Message.error(message="无效的状态值", code=ErrorCode.BAD_REQUEST)

        # 检查字典是否存在且状态正常
        dict_obj = db.query(SYSDict).filter(
            SYSDict.id == dict_id,
            SYSDict.status == DictStatus.NORMAL.value
        ).first()
        if not dict_obj:
            return Message.error(message="字典不存在或已禁用", code=ErrorCode.BAD_REQUEST)

        # 检查字典项是否存在且属于该字典
        dict_item = db.query(SYSDictItem).filter(
            SYSDictItem.item_code == item_code,
            SYSDictItem.dict_id == dict_obj.id
        ).first()
        if not dict_item:
            return Message.error(message="字典项不存在", code=ErrorCode.BAD_REQUEST)

        if dict_item.status == status:
            return Message.error(message=f"当前字典项状态未改变,无需更改", code=ErrorCode.BAD_REQUEST)

        dict_item.status = status
        dict_item.last_time = int(time.time())
        db.commit()
        db.refresh(dict_item)

        status_text = "启用" if status == DictStatus.NORMAL.value else "禁用"
        return Message.success(data=dict_item.to_dict(), message=f"字典项{status_text}成功")
    except SQLAlchemyError as e:
        db.rollback()
        globalLogger.error(f"{SYSTEM_ERROR['DATABASE_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["DATABASE_ERROR"], code=ErrorCode.DATABASE_ERROR)
    except Exception as e:
        globalLogger.error(f"{SYSTEM_ERROR['SYSTEM_ERROR']}: {str(e)}")
        return Message.error(message=SYSTEM_ERROR["SYSTEM_ERROR"], code=ErrorCode.SYSTEM_ERROR)
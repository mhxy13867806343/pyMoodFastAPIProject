from sqlalchemy.orm import Session
from .model import UserPosts
from typing import List


# 构建查询条件的辅助函数
def getBuildQuery(session: Session, title: str = '', status: int = 0, delete: int = 0, uid: int = 0):
    query = session.query(UserPosts)

    # 如果提供了uid，则添加uid过滤条件
    if uid:
        query = query.filter(UserPosts.user_id == uid)

    # 添加其他可能的过滤条件
    if title:
        query = query.filter(UserPosts.title.like('%' + title + '%'))
    if status:
        query = query.filter(UserPosts.status == status)
    if delete:
        query = query.filter(UserPosts.isDeleted == delete)

    return query


# 获取邮件列表，支持灵活的查询条件
def getDynamicList(session: Session, title: str = '', status: int = 0, delete: int = 0, pageNum: int = 1,
                   pageSize: int = 20, uid: int = 0) -> List:
    query = getBuildQuery(session, title, status, delete, uid)
    # 计算跳过的记录数
    resultSum = (pageNum - 1) * pageSize
    result = query.offset(resultSum).limit(pageSize).all()
    return result


# 获取满足条件的总条数
def getDynamicTotal(session: Session, title: str = '', status: int = 0, delete: int = 0, uid: int = 0) -> int:
    query = getBuildQuery(session, title, status, delete, uid)
    total = query.count()
    return total

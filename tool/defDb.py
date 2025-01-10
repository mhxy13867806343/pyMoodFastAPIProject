from fastapi import HTTPException,status
from sqlalchemy.exc import SQLAlchemyError
from tool.classDb import httpStatus
from functools import wraps

def dbSessionCommitClose(db,error="操作失败"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
                db.commit()
                return response
            except SQLAlchemyError as e:
                db.rollback()
                # 根据您的情况，这里可以抛出 HTTPException 或返回自定义错误响应
                return httpStatus(message=error or status.HTTP_400_BAD_REQUEST, data={})
            finally:
                db.close()
        return wrapper
    return decorator
def isAdminOrTypeOne(type: int=0) -> bool:
    return type==0
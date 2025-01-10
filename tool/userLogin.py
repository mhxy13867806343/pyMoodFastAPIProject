from fastapi import APIRouter,Depends,status,Query
from models.user.model import AccountInputs
from tool.classDb import httpStatus
from tool.token import pase_token

def isLogin(user: AccountInputs = Depends(pase_token)):
    if user is None or not getattr(user, 'id', None):
        return httpStatus(message="当前用户未登录", data={})
    return user
from fastapi import APIRouter,Depends,status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import time
from datetime import datetime, timedelta

from tool.dbConnectionConfig import sendBindEmail, getVerifyEmail

from tool.dbTools import getValidate_email
from tool.msg import msg
from .model import AccountInputFirst, AccountInputEamail, AccountInputEamail1, AccountInputEamail2
from tool.db import getDbSession
from tool import token as createToken
from models.user.model import AccountInputs
from tool.classDb import httpStatus, validate_pwd
from dantic.pyBaseModels import AccountInput
from tool.dbRedis import RedisDB
from tool.statusTool import EXPIRE_TIME

redis_db = RedisDB()
expires_delta = timedelta(minutes=EXPIRE_TIME)
userApp = APIRouter()
@userApp.post('/registered',description="h5注册",summary="h5注册")
def registered(acc:AccountInput,db:Session = Depends(getDbSession)):
    account:str=acc.account
    password:str=acc.password
    if not account or not password:
        return httpStatus(message=msg.get('error2'), data={})
    existing_account = db.query(AccountInputs).filter(AccountInputs.account == account).first()
    if existing_account is None:
        rTime = int(time.time())
        name=str('--')+str(rTime)+str(account)+str('--')
        password = createToken.getHashPwd(password)
        resultSql = AccountInputs(account=account, password=password, create_time=rTime,
                                    last_time=rTime,name=name,type=1,status=0,sex=0)
        db.add(resultSql)
        db.commit()
        db.flush()
        return httpStatus(code=status.HTTP_200_OK, message=msg.get('ok0'), data={})
    return httpStatus(message=msg.get("error1"), data={})



@userApp.post('/login', description="登录用户信息", summary="登录用户信息")
def login(user_input: AccountInput, session: Session = Depends(getDbSession)):
    account = user_input.account
    password = user_input.password
    newAccount=f"user-{account}"#redis key
    if not account or not password:
        return httpStatus(message=msg.get("error2"), data={})
    # 先从Redis尝试获取用户信息
    user_data = redis_db.get(newAccount)
    if user_data:
        if user_data.get('status')=="1" or int(user_data.get('status'))==1:
            return httpStatus(message=msg.get('accountstatus'), data={})
        try:
            # 验证token的有效性
            user_id = createToken.pase_token(user_data['token'])
            # 如果提供的账号与Redis中的账号一致，且token有效，认为登录成功
            if user_id and account == user_data["account"]:
                user_data['status']=int(user_data['status'])
                user_data['type']=int(user_data['type'])
                user_data['createTime']=int(user_data['createTime'])
                user_data['lastTime']=int(user_data['lastTime'])
                user_data["email"]=user_data.get("email")
                user_data["emailStatus"]=int(user_data.get("emailStatus"))
                user_data['sex']=int(user_data.get("sex"))
                return httpStatus(code=status.HTTP_200_OK, message="登录成功", data=user_data)
            return httpStatus(message=msg.get("tokenstatus"), data={})
        except Exception as e:
            print(e)
            return httpStatus(message=msg.get("tokenstatus"), data={})
    existing_user = session.query(AccountInputs).filter(AccountInputs.account == account).first()
    if existing_user is None or not createToken.check_password(password, existing_user.password):
        return httpStatus(message=msg.get('error0'), data={})
    if existing_user.status=='1' or int(existing_user.status)==1:
        return httpStatus(message=msg.get('accountstatus'), data={})
    try:
        # 用户验证成功，创建token等操作
        token = createToken.create_token({"sub": str(existing_user.id)}, expires_delta)
        user_data = {
            "token": token,
            "type": int(existing_user.type),
            "account": existing_user.account,
            "createTime": int(existing_user.create_time),
            "lastTime": int(existing_user.last_time),
            "name": existing_user.name,
            "status": int(existing_user.status),
            "email": existing_user.email,
            "emailStatus": int(existing_user.emailStatus),
            "sex":int(existing_user.sex)
        }
        # 将用户信息保存到Redis
        redis_db.set(newAccount, user_data)  # 注意调整为合适的键值和数据
        return httpStatus(code=status.HTTP_200_OK, message=msg.get('login0'), data=user_data)
    except Exception as e:
        session.rollback()
        return httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=msg.get("login1"), data={})



@userApp.post('/info',description="获取用户信息",summary="获取用户信息")
def getUserInfo(user: AccountInputs = Depends(createToken.pase_token),session: Session = Depends(getDbSession)):
    if not user:
        return httpStatus(message=msg.get('error31'), data={},code=status.HTTP_401_UNAUTHORIZED)
    datas = session.query(AccountInputs).filter(AccountInputs.id == user).first()

    redis_key = f"user-{datas.account}"  # 构造一个基于用户ID的Redis键
    # 尝试从Redis获取用户信息
    redis_user_data = redis_db.get(redis_key)

    if redis_user_data:
        if redis_user_data.get('status') == 1:
            return httpStatus(message=msg.get('accountstatus'), data={})
        # 如果在Redis中找到了用户信息，直接使用这些信息构建响应
        data_source = {
            "account": redis_user_data.get('account'),
            "name": redis_user_data.get("name"),
            "type": int(redis_user_data.get('type')),
            "createTime": int(redis_user_data.get("createTime")),
            "lastTime": int(redis_user_data.get("lastTime")),
            "id": user,
            "isPermissions": 1,
            "email": redis_user_data.get("email"),
            "status": redis_user_data.get("status"),
            "emailStatus": int(redis_user_data.get("emailStatus")),
            "sex": int(redis_user_data.get("sex"))
        }
        return httpStatus(code=status.HTTP_200_OK, message=msg.get("ok99"), data=data_source)
    else:
        user = session.query(AccountInputs).filter(AccountInputs.id == user).first()
        if user is None:
            return httpStatus(message=msg.get("error3"), data={})
        if user.status == 1:
            return httpStatus(message=msg.get('accountstatus'), data={})
        data_source = {
            "account": user.account,
            "name": user.name,
            "type": int(user.type),
            "createTime": int(user.create_time),
            "lastTime": int(user.last_time),
            "id": user,
            "isPermissions": 1,
            "email": user.email,
            "status": user.status,
            "emailStatus": int(user.emailStatus),
            "sex": int(user.sex)
        }
        return httpStatus(code=status.HTTP_200_OK, message=msg.get("ok99"), data=data_source)



@userApp.post('/update',description="更新用户信息",summary="更新用户信息")
def updateUserInfo(params: AccountInputFirst, user: AccountInputs = Depends(createToken.pase_token),session: Session = Depends(getDbSession)):
    if not user:
        return httpStatus(message=msg.get('error31'), data={},code=status.HTTP_401_UNAUTHORIZED)
    name = params.name
    sex=params.sex
    if not name:
        return httpStatus(message=msg.get("error4"), data={})
    db=session.query(AccountInputs).filter(AccountInputs.id==user).first()
    if db is None:
        return httpStatus(message=msg.get("error5"), data={})
    if db.status == 1:
        return httpStatus(message=msg.get('accountstatus'), data={})
    try:
        db.name=name
        db.sex=sex
        session.commit()
        newAccount = f"user-{db.account}"  # redis key
        redis_db.set(newAccount,{
            "name":name,
            "sex":sex  or 0
        })
        return httpStatus(code=status.HTTP_200_OK, message=msg.get("update0"), data={})
    except SQLAlchemyError as e:
        session.rollback()
        return httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=msg.get("update1"), data={})
@userApp.post('/logout',description="用户退出",summary="用户退出")
def logout(user: AccountInputs = Depends(createToken.pase_token),session: Session = Depends(getDbSession)):
    if not user:
        return httpStatus(message=msg.get('error31'), data={},code=status.HTTP_401_UNAUTHORIZED)
    db = session.query(AccountInputs).filter(AccountInputs.id == user).first()
    redis_key = f"user-{db.account}"
    if not redis_key:
        return httpStatus(message=msg.get("loguto0"), data={})
    if db is None:
        return httpStatus(message=msg.get("loguto0"), data={})
    if db.status == 1:
        return httpStatus(message=msg.get('accountstatus'), data={})
    redis_db.delete(redis_key)
    return httpStatus(code=status.HTTP_200_OK, message=msg.get("login01"), data={})

@userApp.post("/bind",description="绑定用户邮箱",summary="绑定用户邮箱")
async def addEmail(params:AccountInputEamail1, user: AccountInputs = Depends(createToken.pase_token),session: Session = Depends(getDbSession)):
    if not user:
        return httpStatus(message=msg.get('error31'), data={},code=status.HTTP_401_UNAUTHORIZED)
    email=params.email
    code=params.code
    if not email:
        return httpStatus(message=msg.get("email00"), data={})
    result:bool=getValidate_email(email) #验证邮箱格式
    if not result:
        return httpStatus(message=msg.get("email01"), data={})
    if not code:
        return httpStatus(message=msg.get("email023"), data={})
    result: dict = await getVerifyEmail(email,code, user)
    if not result:
        return httpStatus(message=msg.get("email024"), data={})
    if result.get('code')==-800 or result.get('code')==-801 or  result.get('code')==-802:
        return httpStatus(message=result.get("message"), data={})
    resultSql = session.query(AccountInputs).filter(AccountInputs.id == user)
    if not resultSql.first():
        return httpStatus(message=msg.get("email02"), data={})
    if resultSql.first().status == 1:
        return httpStatus(message=msg.get("accountstatus"), data={})
    existing_email_user = session.query(AccountInputs).filter(AccountInputs.email == email).first()
    if existing_email_user:
        return httpStatus(message=msg.get("email021"), data={})
    try:
        if result.get("code")==200:
            resultSql.first().email=email
            resultSql.first().emailStatus=1
            session.commit()
            redis_key = f"user-{resultSql.first().account}"  # 构造一个基于用户ID的Redis键
            user_data = redis_db.get(redis_key)
            if user_data:
                user_data["email"]=email
                user_data["emailStatus"]=1
                redis_db.set(redis_key, user_data)
            return httpStatus(code=status.HTTP_200_OK, message=msg.get("email09901"), data={})
        return httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=msg.get("email09902"), data={})
    except SQLAlchemyError as e:
        session.rollback()
        return httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=msg.get("email09902"), data={})



@userApp.post("/verify",description="发送用户邮箱验证码",summary="发送用户邮箱验证码")
async def verifyEmail(params:AccountInputEamail, user: AccountInputs = Depends(createToken.pase_token),session: Session = Depends(getDbSession)):
    if not user:
        return httpStatus(message=msg.get('error31'), data={},code=status.HTTP_401_UNAUTHORIZED)
    if not params.email:
        return httpStatus(message=msg.get("email00"), data={})
    sendEmail =  sendBindEmail(params.email,user)
    message = sendEmail.get("message")
    code = sendEmail.get("code")
    if not code:
        return httpStatus(message=msg.get("email023"), data={})
    if code!=200:
        return httpStatus(message=message, data={})
    return httpStatus(code=status.HTTP_200_OK, message="发送成功", data={})

@userApp.post("/verifyCode",description="验证用户邮箱验证码",summary="验证用户邮箱验证码")
async def verifyCode(params:AccountInputEamail1, user: AccountInputs = Depends(createToken.pase_token),session: Session = Depends(getDbSession)):
    if not user:
        return httpStatus(message=msg.get('error31'), data={},code=status.HTTP_401_UNAUTHORIZED)
    email=params.email
    code=params.code
    if not email:
        return httpStatus(message=msg.get("email00"), data={})
    if not code:
        return httpStatus(message=msg.get("email023"), data={})

    db = session.query(AccountInputs).filter(AccountInputs.id == user).first()

    if email!=db.email:
        return httpStatus(message=msg.get("email022"), data={})

    result: dict = await getVerifyEmail(email, code, db.id)
    message = result.get("message")
    if db.status==1:
        return httpStatus(message=msg.get("accountstatus"), data={})
    if db.emailStatus==0:
        return httpStatus(message=msg.get("email001"), data={})
    if code != 0:
        return httpStatus(message=message, code=code, data={})
    return httpStatus(message=msg.get("changeVerifyCode1"), data={})

@userApp.post("/resetpwd",description="重置密码",summary="重置密码")
async def resetPwd(params:AccountInputEamail2, user: AccountInputs = Depends(createToken.pase_token),session: Session = Depends(getDbSession)):
    if not user:
        return httpStatus(message=msg.get('error31'), data={},code=status.HTTP_401_UNAUTHORIZED)
    email=params.email
    code=params.code
    password=params.password
    if not email:
        return httpStatus(message=msg.get("email00"), data={})
    db=session.query(AccountInputs).filter(AccountInputs.id==user).first()
    if email!=db.email:
        return httpStatus(message=msg.get("email022"), data={})
    if not password:
        return httpStatus(message=msg.get("email09903"), data={})
    if not code:
        return httpStatus(message=msg.get("email09904"), data={})
    result: dict =await getVerifyEmail(email, code,db.id)
    code = result.get("code")
    message = result.get("message")
    if db.status==1:
        return httpStatus(message=msg.get("accountstatus"), data={})
    if db.emailStatus==0:
        return httpStatus(message=msg.get("email001"), data={})
    if code==200:
        try:
            db.password = createToken.getHashPwd(password)
            db.last_time=int(time.time())
            session.commit()
            return httpStatus(code=status.HTTP_200_OK, message=msg.get("updatdpwd"), data={})
        except SQLAlchemyError as e:
            session.rollback()
            return httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=msg.get("updatdpwd001"), data={})
    else:
        return httpStatus(message=message, code=code, data={})

#没有用户信息的
@userApp.get("/recoverEmail",description="通过验证码找回密码",summary="通过验证码找回密码")
async def getRecoverPwd(email, session: Session = Depends(getDbSession)):
    if not email:
        return httpStatus(message=msg.get("email00"), data={})
    db = session.query(AccountInputs).filter(AccountInputs.email == email).first()
    if not db or db.status==1 or db.emailStatus==0:
        return httpStatus(message=msg.get("verify99"), data={})
    sendEmail = sendBindEmail(email, f"recover{db.id}")
    message = sendEmail.get("message")
    code = sendEmail.get("code")
    if not code:
        return httpStatus(message=msg.get("email023"), data={})
    if code != 200:
        return httpStatus(message=message, data={})
    return httpStatus(code=status.HTTP_200_OK, message=msg.get('changeVerifyCode2'), data={})
@userApp.post("/recPassVerify",description="找回密码",summary="找回密码")
async def postRecoVerify(p:AccountInputEamail2, session: Session = Depends(getDbSession)):
    email=p.email
    code=p.code
    password=p.password
    if not email:
        return httpStatus(message=msg.get("email00"), data={})
    if not code:
        return httpStatus(message=msg.get("email023"), data={})
    if not password:
        return httpStatus(message=msg.get("email09903"), data={})
    db=session.query(AccountInputs).filter(AccountInputs.email == email).first()
    if not db or db.status==1 or db.emailStatus==0:
        return httpStatus(message=msg.get("verify99"), data={})
    result=await getVerifyEmail(email, code, f"recover{db.id}")
    code = result.get("code")
    message = result.get("message")
    if code==200:
        try:
            db.password = createToken.getHashPwd(password)
            db.last_time=int(time.time())
            session.commit()
            return httpStatus(code=status.HTTP_200_OK, message=msg.get("updatdpwd"), data={})
        except SQLAlchemyError as e:
            session.rollback()
            return httpStatus(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=msg.get("updatdpwd001"), data={})
    else:
        return httpStatus(message=message, code=code, data={})
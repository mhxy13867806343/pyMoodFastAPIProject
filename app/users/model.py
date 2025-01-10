from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union, TypeVar, Type, Callable, cast

class AccountInputFirst(BaseModel):
    name: Optional[str] = None
    sex: Optional[str] = None
class AccountInputEamail(BaseModel):
    email: Optional[str] = None

class AccountInputEamail1(AccountInputEamail):
    code: Optional[str] = None
class AccountInputEamail2(BaseModel):
    password: Optional[str] = None
    email: Optional[str] = None
    code: Optional[str] = None

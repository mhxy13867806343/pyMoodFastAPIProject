from starlette import status
from typing import Tuple, List, Dict, Any
from tool.classDb import HttpStatus


def getArgsKwArgsResult(*args, **kwargs)->Dict[str, Any]:
    """
    Get the arguments and keyword arguments and return them as a dictionary
    :param args:  无名参数
    :param kwargs:  有名参数 如：name="zhangsan"
    :return: 返回一个字典
    """
    result = {
        **kwargs,
        "total": kwargs.get("total",0),
        "data": kwargs.get("data",[]),
        "pageNum": kwargs.get("pageNum",1),
        "pageSize": kwargs.get("pageSize",10),
    }

    return HttpStatus.success(message="获取成功", data=result)

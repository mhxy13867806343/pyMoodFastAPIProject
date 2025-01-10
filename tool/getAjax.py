import requests
import json
from datetime import datetime

from fastapi import status

from tool.dbHeaders import outerUserAgentHeadersX64
from tool.dbUrlResult import holidayYearUrl


def getHeadersHolidayUrl(year:int=datetime.now().year):
    url=f"{holidayYearUrl}{year}"
    holidayApi=requests.get(url,headers=outerUserAgentHeadersX64).content
    api=json.loads(holidayApi)

    if api['code']==-1:
        return {
            "data":{
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "服务出错",
            }

        }
    if api['code']==0:
        if len(api['holiday']) == 0:
            return {
                "data":{
                    "code": -80000,
                    "message": "暂无数据",
                }
            }
        return {
            "data":{
                "code": status.HTTP_200_OK,
                "message": "获取成功",
                "result": api['holiday'],
            }
        }
    return {
        "data":{
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "服务出错",
        }
    }
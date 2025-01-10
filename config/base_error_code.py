from fastapi import status

# 基础错误码常量
SUCCESS = status.HTTP_200_OK
BAD_REQUEST = status.HTTP_400_BAD_REQUEST
UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
FORBIDDEN = status.HTTP_403_FORBIDDEN
NOT_FOUND = status.HTTP_404_NOT_FOUND
METHOD_NOT_ALLOWED = status.HTTP_405_METHOD_NOT_ALLOWED
VALIDATION_ERROR = status.HTTP_422_UNPROCESSABLE_ENTITY
TOO_MANY_REQUESTS = status.HTTP_429_TOO_MANY_REQUESTS
INTERNAL_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
DB_ERROR = status.HTTP_503_SERVICE_UNAVAILABLE
REDIS_ERROR = status.HTTP_503_SERVICE_UNAVAILABLE
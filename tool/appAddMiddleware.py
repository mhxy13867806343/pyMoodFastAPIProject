from fastapi.middleware.cors import CORSMiddleware # CORS
def appAddMiddleware(app):
    # 将 router 添加到 app 中
    origins = [
        "*"

    ]  # 也可以设置为"*"，即为所有。
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # 允许访问的源
        allow_credentials=True,  # 支持 cookie
        allow_methods=["*"],  # 允许使用的请求方法
        allow_headers=["*"]  # 允许携带的 Headers
    )
    return app
from fastapi.middleware.cors import CORSMiddleware

def appAddMiddleware(app):
    # 配置允许的源
    origins = [
        "https://lcs200.icu",  # 生产环境
        "http://localhost:8000",  # 本地开发
        "http://127.0.0.1:8000"   # 本地开发
    ]

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # 限制允许的源
        allow_credentials=True,  # 允许携带凭证
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 限制允许的HTTP方法
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With"
        ],  # 限制允许的请求头
        expose_headers=[
            "Content-Length",
            "X-Rate-Limit"
        ],  # 允许浏览器访问的响应头
        max_age=600  # 预检请求结果缓存时间（秒）
    )
    return app
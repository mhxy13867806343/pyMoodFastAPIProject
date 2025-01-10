from .dbThrottling import limiter, rate_limit_exceeded_handler,RateLimitExceeded
def appLimitRate(app):

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    return app
import logging
# 设置全局日志记录器
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
globalLogger = logging.getLogger(__name__)
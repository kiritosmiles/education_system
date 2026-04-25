import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件，记录每个请求的方法、路径、状态码和耗时"""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        duration = (time.time() - start_time) * 1000

        # 获取客户端IP
        client_ip = request.client.host if request.client else "-"

        # 记录日志
        logger.info(
            f'{client_ip} - {request.method} {request.url.path} - '
            f'状态码: {response.status_code} - 耗时: {duration:.2f}ms'
        )

        return response

import time
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

class CustomRetryMiddleware(RetryMiddleware):
    def process_response(self, request, response, spider):
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            retry_times = request.meta.get('retry_times', 0)
            wait_time = 2 ** retry_times  # Exponential backoff
            time.sleep(wait_time)
            return self._retry(request, reason, spider) or response
        return response

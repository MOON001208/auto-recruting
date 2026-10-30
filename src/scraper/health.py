class SearchHealth:
    """검색 요청 실패를 기록하고 반복 장애로 인한 지연을 제한한다."""
    def reset_health(self):
        self.attempts = 0
        self.failures = 0
        self.consecutive_failures = 0
        self.last_error = ''

    def search_succeeded(self):
        self.attempts += 1
        self.consecutive_failures = 0

    def search_failed(self, reason):
        self.attempts += 1
        self.failures += 1
        self.consecutive_failures += 1
        self.last_error = reason

    def should_stop(self):
        return self.consecutive_failures >= 3

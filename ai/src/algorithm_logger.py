import time


class AlgorithmLogger:
    """Log hiển thị trên màn hình với hỗ trợ cuộn và chống spam."""

    _logs = []
    _pinned_logs = []
    _has_new_log = True
    _is_enabled = True

    _max_logs = 120
    _max_pinned_logs = 10
    _cooldowns = {}
    _default_gameplay_cooldown = 10.0

    _scroll_offset = 0
    _visible_line_count = 24

    @classmethod
    def clear(cls):
        cls._logs.clear()
        cls._pinned_logs.clear()
        cls._cooldowns.clear()
        cls._scroll_offset = 0
        cls._has_new_log = True

    @classmethod
    def _trim(cls):
        if len(cls._pinned_logs) > cls._max_pinned_logs:
            cls._pinned_logs = cls._pinned_logs[-cls._max_pinned_logs:]
        if len(cls._logs) > cls._max_logs:
            cls._logs = cls._logs[-cls._max_logs:]

    @classmethod
    def _total_lines(cls):
        total = len(cls._pinned_logs) + len(cls._logs)
        if cls._pinned_logs and cls._logs:
            total += 1
        return total

    @classmethod
    def _clamp_scroll(cls):
        max_offset = max(0, cls._total_lines() - cls._visible_line_count)
        if cls._scroll_offset > max_offset:
            cls._scroll_offset = max_offset
        if cls._scroll_offset < 0:
            cls._scroll_offset = 0

    @classmethod
    def log(cls, message):
        if not cls._is_enabled:
            return
        cls._logs.append(message)
        cls._trim()
        cls._clamp_scroll()
        cls._has_new_log = True

    @classmethod
    def pin(cls, message):
        if not cls._is_enabled:
            return
        cls._pinned_logs.append(message)
        cls._trim()
        cls._clamp_scroll()
        cls._has_new_log = True

    @classmethod
    def log_once_per_key(cls, key, message, cooldown=None, group=None):
        if not cls._is_enabled:
            return
        if cooldown is None:
            cooldown = cls._default_gameplay_cooldown

        now = time.time()
        last_time = cls._cooldowns.get(key, 0)
        if now - last_time >= cooldown:
            cls._cooldowns[key] = now
            cls.log(message)

    @classmethod
    def set_enabled(cls, enabled: bool):
        cls._is_enabled = enabled
        cls._has_new_log = True

    @classmethod
    def set_visible_line_count(cls, count: int):
        cls._visible_line_count = max(1, count)
        cls._clamp_scroll()
        cls._has_new_log = True

    @classmethod
    def scroll_up(cls, amount: int = 1):
        cls._scroll_offset = max(0, cls._scroll_offset - amount)
        cls._has_new_log = True

    @classmethod
    def scroll_down(cls, amount: int = 1):
        cls._clamp_scroll()
        max_offset = max(0, cls._total_lines() - cls._visible_line_count)
        cls._scroll_offset = min(max_offset, cls._scroll_offset + amount)
        cls._has_new_log = True

    @classmethod
    def scroll_to_bottom(cls):
        cls._clamp_scroll()
        cls._scroll_offset = max(0, cls._total_lines() - cls._visible_line_count)
        cls._has_new_log = True

    @classmethod
    def get_logs(cls):
        if cls._pinned_logs and cls._logs:
            return cls._pinned_logs + [""] + cls._logs
        if cls._pinned_logs:
            return cls._pinned_logs
        return cls._logs

    @classmethod
    def get_visible_logs(cls):
        lines = cls.get_logs()
        cls._clamp_scroll()
        start = cls._scroll_offset
        end = start + cls._visible_line_count
        return lines[start:end]

    @classmethod
    def get_scrollbar_state(cls):
        total = cls._total_lines()
        visible = cls._visible_line_count
        cls._clamp_scroll()
        return {
            'total_lines': total,
            'visible_lines': visible,
            'scroll_offset': cls._scroll_offset,
            'max_offset': max(0, total - visible),
        }

    @classmethod
    def check_and_reset_flag(cls):
        if cls._has_new_log:
            cls._has_new_log = False
            return True
        return False

from datetime import datetime


def parse_time(time_str):
    if not time_str:
        return None
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def check_lock_time(period1_start, period1_end, period2_start, period2_end,
                    mode="lock_period", now=None):
    now = now or datetime.now()
    current_minutes = now.hour * 60 + now.minute

    p1_start_mins = parse_time(period1_start)
    p1_end_mins = parse_time(period1_end)
    p2_start_mins = parse_time(period2_start)
    p2_end_mins = parse_time(period2_end)

    def in_period(start_mins, end_mins):
        if start_mins is None or end_mins is None:
            return False
        if start_mins <= end_mins:
            return start_mins <= current_minutes < end_mins
        else:
            return current_minutes >= start_mins or current_minutes < end_mins

    in_period1 = in_period(p1_start_mins, p1_end_mins)
    in_period2 = in_period(p2_start_mins, p2_end_mins)

    if mode == "unlock_period":
        return not in_period1 and not in_period2
    return in_period1 or in_period2

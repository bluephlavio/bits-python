def floor_filter(value):
    return int(value // 1)


def ceil_filter(value):
    return int(value // 1 + (value % 1 > 0))


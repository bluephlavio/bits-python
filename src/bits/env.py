from jinja2 import Environment

env = Environment(
    block_start_string=r"\BLOCK{",
    block_end_string=r"}",
    variable_start_string=r"\VAR{",
    variable_end_string=r"}",
    comment_start_string=r"\#{",
    comment_end_string=r"}",
    line_statement_prefix=r"%%",
    line_comment_prefix=r"%#",
    trim_blocks=True,
    autoescape=False,
)

def floor_filter(value):
    return int(value // 1)

def ceil_filter(value):
    return int(value // 1 + (value % 1 > 0))

env.filters['floor'] = floor_filter
env.filters['ceil'] = ceil_filter

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

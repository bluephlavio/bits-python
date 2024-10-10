# Custom filters for jinja2 templates


def floor_filter(value):
    return int(value // 1)


def ceil_filter(value):
    return int(value // 1 + (value % 1 > 0))


def getitem_filter(index, values, start=1):
    return values[index - start]


def pick_filter(items, picklist, start=1):
    if not picklist:
        return items
    picked_items = []
    for pick in picklist:
        index = pick - start
        if index < len(items):
            picked_items.append(items[index])
    return picked_items


def render_filter(item):
    from .block import Block  # pylint: disable=import-outside-toplevel

    if isinstance(item, Block):
        return item.render()
    return item


def enumerate_filter(items, opts=""):
    return (
        r"\begin{enumerate}"
        + f"[{opts}]"
        + "\n"
        + "\n".join([r"\item " + render_filter(item) for item in items])
        + "\n"
        + r"\end{enumerate}"
    )


def show_filter(
    items,
    single_item_template="{item}",
    preamble="",
    opts="",
):
    if len(items) == 1:
        return single_item_template.format(item=render_filter(items[0]))
    return preamble + "\n" + enumerate_filter(items, opts=opts)

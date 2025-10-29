def register(env):
    # Port of the previous built-in filters to a plugin for tests

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
        from bits.block import Block  # pylint: disable=import-outside-toplevel

        if isinstance(item, Block):
            return item.render()
        return item

    def enumerate_filter(items, opts=""):
        return (
            r"\\begin{enumerate}"
            + f"[{opts}]"
            + "\n"
            + "\n".join([r"\\item " + render_filter(item) for item in items])
            + "\n"
            + r"\\end{enumerate}"
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

    # Register filters
    env.filters["floor"] = floor_filter
    env.filters["ceil"] = ceil_filter
    env.filters["getitem"] = getitem_filter
    env.filters["pick"] = pick_filter
    env.filters["render"] = render_filter
    env.filters["enumerate"] = enumerate_filter
    env.filters["show"] = show_filter


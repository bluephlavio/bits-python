def register(env):
    # Override existing 'pick' filter with a sentinel behavior
    def pick(items, picklist, start=1):
        return ["OVERRIDE"]

    env.filters["pick"] = pick


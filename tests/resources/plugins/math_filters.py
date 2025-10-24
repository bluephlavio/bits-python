def register(env):
    def double(x):
        return x * 2

    env.filters["double"] = double

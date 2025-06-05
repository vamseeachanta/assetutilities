def decoratorWithArgumentExample(func=None, *, kw1=None):
    """Decotrator with keyword argument Boiler Plate Example"""
    # Standard library imports
    import functools

    @functools.wraps(func)
    def wrapper_decoratorWithArgumentExample(*args, **kwargs):
        cfg = func(*args, **kwargs)
        return cfg

    return wrapper_decoratorWithArgumentExample


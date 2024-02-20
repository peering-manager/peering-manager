from peering_manager.registry import DATA_BACKENDS_KEY, registry

__all__ = ("get_data_backend_choices", "register_data_backend")


def get_data_backend_choices():
    return [
        (None, "---------"),
        *[(name, cls.label) for name, cls in registry[DATA_BACKENDS_KEY].items()],
    ]


def register_data_backend():
    """
    Register a `DataBackend` class.
    """

    def _wrapper(cls):
        registry[DATA_BACKENDS_KEY][cls.name] = cls
        return cls

    return _wrapper

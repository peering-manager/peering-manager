class Registry(dict):
    """
    Central registry for registration of functionality.

    Once a `Registry` is initialized, keys cannot be added or removed (though the
    value of each key is mutable).
    """

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise KeyError(f"Invalid store: {key}")

    def __setitem__(self, key, value):
        raise TypeError("Cannot add stores to registry after initialisation")

    def __delitem__(self, key):
        raise TypeError("Cannot delete stores from registry")


DATA_BACKENDS_KEY = "data_backends"

# Initialize the global registry
registry = Registry(
    {DATA_BACKENDS_KEY: dict(), "model_features": dict(), "views": dict()}
)

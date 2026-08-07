from importlib import import_module

SINK_MODULES: tuple[str, ...] = ("aspect_ratio",)


def register_all() -> None:
    for module_name in SINK_MODULES:
        import_module(f"custom.sink.{module_name}")


__all__ = ["register_all"]

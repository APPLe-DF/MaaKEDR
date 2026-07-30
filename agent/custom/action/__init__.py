from importlib import import_module

ACTION_MODULES = ("general", "ocr_logger", "farm_resources", "pvp")


def register_all() -> None:
    for module_name in ACTION_MODULES:
        import_module(f"custom.action.{module_name}")


__all__ = ["register_all"]

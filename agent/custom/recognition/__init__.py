from importlib import import_module

RECOGNITION_MODULES = ("farm_resources", "pvp", "stamina", "event_stage")


def register_all() -> None:
    for module_name in RECOGNITION_MODULES:
        import_module(f"custom.recognition.{module_name}")


__all__ = ["register_all"]

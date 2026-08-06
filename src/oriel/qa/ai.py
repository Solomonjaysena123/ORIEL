from .adapters import UnsupportedAdapter
class AIAdapter(UnsupportedAdapter):
    """Base adapter for deterministic AI evaluation checks."""
    domain = "ai"

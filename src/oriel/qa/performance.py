from .adapters import UnsupportedAdapter
class PerformanceAdapter(UnsupportedAdapter):
    """Base adapter for load and benchmark checks."""
    domain = "performance"

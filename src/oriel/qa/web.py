from .adapters import UnsupportedAdapter
class WebAdapter(UnsupportedAdapter):
    """Base adapter for browser checks."""
    domain = "web"

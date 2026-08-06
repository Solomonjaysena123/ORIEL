from .adapters import UnsupportedAdapter
class APIAdapter(UnsupportedAdapter):
    """Base adapter for HTTP/API contract checks."""
    domain = "api"

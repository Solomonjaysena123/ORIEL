from .adapters import UnsupportedAdapter
class MobileAdapter(UnsupportedAdapter):
    """Base adapter for device checks."""
    domain = "mobile"

from .adapters import UnsupportedAdapter
class SecurityAdapter(UnsupportedAdapter):
    """Base adapter for authorized security checks."""
    domain = "security"

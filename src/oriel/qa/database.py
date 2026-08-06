from .adapters import UnsupportedAdapter
class DatabaseAdapter(UnsupportedAdapter):
    """Base adapter for database checks."""
    domain = "database"

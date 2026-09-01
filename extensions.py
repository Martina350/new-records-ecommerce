"""Extensiones Flask sin enlazarlas a una instancia concreta."""

from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
migrate = Migrate(compare_type=True)

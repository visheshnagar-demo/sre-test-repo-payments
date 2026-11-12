"""Server package with app alias compatibility."""

import sys
from . import calculator, main, models

sys.modules.setdefault("app", sys.modules[__name__])
sys.modules.setdefault("app.calculator", calculator)
sys.modules.setdefault("app.main", main)
sys.modules.setdefault("app.models", models)

"""Tests package."""
import sys
import server
import server.calculator
import server.main
import server.models

sys.modules.setdefault("app", server)
sys.modules.setdefault("app.calculator", server.calculator)
sys.modules.setdefault("app.main", server.main)
sys.modules.setdefault("app.models", server.models)

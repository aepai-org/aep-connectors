"""Built-in connector adapters."""

from .hermes import HermesAdapter
from .http import HTTPAdapter
from .openclaw import OpenClawAdapter

__all__ = ["HTTPAdapter", "HermesAdapter", "OpenClawAdapter"]

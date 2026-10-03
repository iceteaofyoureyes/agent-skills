"""Bind historical import paths to the physical shared implementation."""
import importlib
import sys


def retain_legacy_identity(core_name, legacy_name):
    """One module/global namespace, including private symbols and pickle names.

    Register before dataclass definitions so both import orders use the same
    historical class identity. Keep the core import spec and physical source.
    """
    module = sys.modules[core_name]
    parent_name, separator, child_name = legacy_name.rpartition('.')
    # Dotted imports also traverse parent attributes. These package initializers
    # contain no runtime imports; never load the historical adapter recursively.
    parent = None
    if separator:
        try:
            parent = importlib.import_module(parent_name)
        except ModuleNotFoundError as error:
            # A standalone BA payload has no tooling package. Shared path and
            # persistence contracts remain usable without importing a kit.
            if error.name != parent_name and not parent_name.startswith(error.name + '.'):
                raise
    module.__name__ = legacy_name
    sys.modules[legacy_name] = module
    if parent is not None:
        setattr(parent, child_name, module)

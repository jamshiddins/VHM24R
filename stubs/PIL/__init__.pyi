# Type stubs for PIL (Pillow)

# Re-export Image module for proper import resolution
from . import Image as Image
from .Image import Image as ImageClass

# Common PIL modules
__version__: str

# Make PIL importable
def __getattr__(name: str) -> object: ...

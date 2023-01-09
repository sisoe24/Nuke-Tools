from . import logger

try:
    import nuke
    import nukescripts
except ImportError:
    from src.local import local_nuke as nuke
else:
    from . import main

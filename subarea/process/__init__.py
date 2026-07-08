"""subarea.process — pipeline stages: prepare | kernel_run | trajectory_read |
gateway_od | cbi | visualize. Production entry: python -m subarea.process run <yml>.
Stage status (FR-19 v2 implementation order): prepare=IMPLEMENTED, kernel_run=stub
(awaits kernel DTAT streamer, step 3), later stages=stubs (steps 4-5)."""
from .config import load_config
from .prepare import prepare

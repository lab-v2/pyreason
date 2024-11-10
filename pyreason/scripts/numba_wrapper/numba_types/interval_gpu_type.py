from numba import types, float32
from numba.core.extending import typeof_impl, type_callable, models, register_model, make_attribute_wrapper
from numba.core import cgutils
from pyreason.scripts.interval.interval_gpu import IntervalGPU  # Import IntervalGPU class here

# Define the IntervalGPUType
class IntervalGPUType(types.Type):
    def __init__(self):
        super().__init__(name="IntervalGPU")

# Create a single instance of IntervalGPUType
interval_gpu_type = IntervalGPUType()

# Associate IntervalGPU class with interval_gpu_type
@typeof_impl.register(IntervalGPU)
def typeof_interval(val, c):
    return interval_gpu_type

# Type the constructor
@type_callable(IntervalGPU)
def type_interval_gpu(context):
    def typer(lo, hi):
        if isinstance(lo, types.Float) and isinstance(hi, types.Float):
            return interval_gpu_type
    return typer

# Register a data model for IntervalGPU
@register_model(IntervalGPUType)
class IntervalGPUModel(models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('l', float32),  # Lower bound
            ('u', float32)   # Upper bound
        ]
        super().__init__(dmm, fe_type, members)

# Enable attribute access
make_attribute_wrapper(IntervalGPUType, 'l', 'l')
make_attribute_wrapper(IntervalGPUType, 'u', 'u')

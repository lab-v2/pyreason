# Changed: used to be the Numba WorldType boxing/unboxing circus.
# Just re-exports the plain Python World now.
from pyreason.scripts.components.world import World

world_type = World
WorldType = World

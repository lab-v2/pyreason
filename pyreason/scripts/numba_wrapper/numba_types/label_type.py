# Changed: this used to be the big Numba type registration file.
# Now it's just a re-export of the plain Python Label — same import path so
# nothing else had to move.
from pyreason.scripts.components.label import Label

label_type = Label
LabelType = Label

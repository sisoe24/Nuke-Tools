import os
from .color_widgets import color_widget


tmp_utils = os.path.join(os.path.dirname(__file__), '.tmp')
if not os.path.exists(tmp_utils):
    os.mkdir(tmp_utils)

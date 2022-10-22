# coding: utf-8
from __future__ import print_function

import os
from random import randint

from PySide2.QtGui import QColor, QPalette


def color_widget(color=None):
    """Color widgets layout.

    **NOTE** this wrapper must be called with the parenthesis: `@color_widget()`

    Example:
        - `@color_widget(Qt.blue)`: Blue color
        - `@color_widget(QColor(255, 0, 0))`: Red color
        - `@color_widget()`: Random color

    Color widgets layout to more easily see widgets boundaries. The function
    accepts a parameter `color` to indicate which color to use for the layout.
    If no parameter are passed, then a random color will be picked.

    Args:
        color (QColor, optional): A color using QColor or Qt base colors.
        Defaults to None.
    """
    def out_wrapper(func):
        def inner_wrapper(*args, **kwargs):
            self = args[0]
            func(*args, **kwargs)

            file = os.path.join(os.path.dirname(__file__),
                                '.tmp', 'widgets_color_state')
            if not os.path.exists(file):
                return

            with open(file) as f:
                if f.read().strip() == 'False':
                    return

            self.setAutoFillBackground(True)
            palette = QPalette()

            if not color:
                palette.setColor(QPalette.Window, QColor(
                    randint(0, 256), randint(0, 256), randint(0, 256)))
            else:
                palette.setColor(QPalette.Window, QColor(color))

            self.setPalette(palette)
        return inner_wrapper
    return out_wrapper

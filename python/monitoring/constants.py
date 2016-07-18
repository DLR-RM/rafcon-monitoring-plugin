
def get_glade_path(glade_file):
    """
    A function to get the path of the chosen glade file
    :param glade_file: The name of the glade file
    :return: the path of the glade file
    """

    from os import path
    mvc_dir = path.dirname(__file__)
    return path.join(mvc_dir, "glade", glade_file)

FONTS = ["DIN Next LT Pro", "FontAwesome"]
INTERFACE_FONT = FONTS[0]
ICON_FONT = FONTS[1]

BUTTON_MIN_WIDTH = 90
BUTTON_MIN_HEIGHT = 40
LETTER_SPACING_NONE = "0"

FONT_SIZE_SMALL = "10"
FONT_SIZE_NORMAL = "12"
FONT_SIZE_BIG = "14"
BUTTON_REFR = "f021"
ICON_SIGNAL = "f012"
ICON_CONFIG = "f013"
ICON_NET_HISTORY = "f017"
ICON_DISCONNECTED = "f0e7"
ICON_DISABLED = "f05e"
ICON_MAIL = "f003"
ICON_NET = "f0ec"


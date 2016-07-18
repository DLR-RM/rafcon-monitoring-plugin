
def get_glade_path(glade_file):
    """
    A function to get the path of the chosen glade file
    :param glade_file: The name of the glade file
    :return: the path of the glade file
    """

    from os import path
    mvc_dir = path.dirname(__file__)
    return path.join(mvc_dir, "glade", glade_file)


def set_icon_and_text(icon, text, color, ping):
    """
    Creates a colored CellRendererText with the chosen icon, an text and the ping
    :param icon: The icon
    :param text: The text
    :param color: The color
    :param ping: the ping
    :return: the created CellRendererText
    """

    markup = '<span {0} font_desc="constants.INTERFACE_FONT font_size=constants.FONT_SIZE_NORMAL" ' \
             '>&#x{1}; {2} ({3})</span>'.format(color, icon, text, ping)
    return markup


BUTTON_REFR = "f021"
ICON_SIGNAL = "f012"
ICON_CONFIG = "f013"
ICON_NET_HISTORY = "f017"
ICON_DISCONNECTED = "f0e7"
ICON_DISABLED = "f05e"
ICON_MAIL = "f003"
ICON_NET = "f0ec"


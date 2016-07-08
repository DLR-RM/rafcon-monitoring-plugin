
def get_glade_path(glade_file):
    from os import path
    mvc_dir = path.dirname(__file__)
    return path.join(mvc_dir, "glade", glade_file)


def set_icon_and_text(icon, text, color, ping):
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
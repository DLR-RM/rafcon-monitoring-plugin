"""
Server view of the monitoring plugin
"""
from gtkmvc import View
from monitoring import constants
from rafcon.gui import gui_helper


class ServerView(View):
    """
    Server view
    """
    builder = constants.get_glade_path('server.glade')
    top = 'network_scrolled_window'
    icons = {'connection': constants.ICON_SIGNAL,
             'config':     constants.ICON_CONFIG,
             'history':     constants.ICON_NET_HISTORY,
             'messages':   constants.ICON_MAIL
             }

    def __init__(self):
        View.__init__(self)
        self.notebook = self['server_notebook']

        for i in range(self.notebook.get_n_pages()):
            child = self.notebook.get_nth_page(i)
            tab_label = self.notebook.get_tab_label(child)
            tab_label_text = tab_label.get_text()
            self.notebook.set_tab_label(child, gui_helper.create_tab_header_label(tab_label_text, self.icons))

        self.refresh_btn = self['refresh_conf_btn']
        self.refresh_btn.set_image(gui_helper.create_button_label(constants.BUTTON_REFR))




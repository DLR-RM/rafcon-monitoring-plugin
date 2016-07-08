# TODO: will be replaced soon
from gtk import ListStore

from monitoring.model.network_model import network_manager_model
from rafcon.utils import log
from monitoring.views.client_connection import ClientView
from rafcon.mvc.controllers.utils.extended_controller import ExtendedController
from acknowledged_udp.config import global_network_config
from monitoring.monitoring_manager import global_monitoring_manager
from monitoring import constants

logger = log.get_logger(__name__)


class ClientController(ExtendedController):
    """Controller handling the client monitoring plugin
    """

    def __init__(self, model, view):
        assert isinstance(view, ClientView)
        ExtendedController.__init__(self, model, view)
        self.connection_list_store = ListStore(str, str, int, str)
        self.global_network_config = global_network_config
        self.config_list_store = ListStore(str, str)
        self._actual_entry = None
        self.list = []
        self.history_list_store = ListStore(str)
        self.message_list_store = ListStore(str)
        self.network_manager_model = model

        self.params = {'CLIENT_UDP_PORT',
                       'SERVER_IP',
                       'SERVER_UDP_PORT',
                       'SPACEBOT_CUP_MODE',
                       'HASH_LENGTH',
                       'SALT_LENGTH',
                       'MAX_TIME_WAITING_FOR_ACKNOWLEDGEMENTS',
                       'MAX_TIME_WAITING_BETWEEN_CONNECTION_TRY_OUTS',
                       'BURST_NUMBER',
                       'TIME_BETWEEN_BURSTS',
                       'SERVER',
                       'HISTORY_LENGTH',
                       'ENABLED',
                       'TYPE',
                       'CLIENT_ID'
                       }

    def register_view(self, view):
        """Called when the View was registered"""

        self.view['value_text'].set_property('editable', True)
        self.view['value_text'].connect('edited', self.on_value_changed)
        self.view['value_text'].connect('editing-started', self.editing_started)
        self.view['value_text'].connect('editing-canceled', self.editing_canceled)

        self.view['history_tree_view2'].set_model(self.history_list_store)
        self.view['message_tree_view1'].set_model(self.message_list_store)

        self.view['connection_tree_view1'].set_model(self.connection_list_store)
        self.view['connect_btn1'].connect('clicked', self.on_connect_button_clicked)
        self.view['disconnect_btn1'].connect('clicked', self.on_disconnect_button_clicked)
        self.view['conf_tree_view'].set_model(self.config_list_store)
        self.view['save_btn'].connect('clicked', self.on_save_button_clicked)

        self.view['load_btn'].connect('clicked', self.on_load_button_clicked)

        self.view['reload_btn'].connect('clicked', self.on_reload_button_clicked)
        self.view['clear_btn'].connect('clicked', self.on_clear_button_clicked)

        self.view['reload_btn1'].connect('clicked', self.on_message_reload_button_clicked)
        self.view['clear_btn1'].connect('clicked', self.on_message_clear_button_clicked)

        self.view['refresh_conf_btn'].connect('clicked', self.on_apply_button_clicked)

        # self.refresh_config()
        self.network_manager_model.set_config_value(None, None)
        self.refresh_con()

    def on_disconnect_button_clicked(self, *args):
        """
        Triggered when disconnect button is clicked
        Disconnects from selected server
        :param args:
        :return:
        """
        path = self.view["connection_tree_view1"].get_cursor()[0]
        if path is not None:
            for index in path:
                address = self.network_manager_model.connected_ip_port[index]
                logger.info("Disconnect from server: {0}".format(address))
                global_monitoring_manager.disconnect(address)
                self.refresh_con()

    def on_connect_button_clicked(self, *args):
        """
        Triggered when connect button clicked
        Connects to selected server
        :param args:
        :return:
        """
        path = self.view["connection_tree_view1"].get_cursor()[0]
        if path is not None:
            for index in path:
                address = self.network_manager_model.connected_ip_port[index]
                logger.info("Connecting to: {0}".format(address))
                if self.network_manager_model.get_connected_status(address) == "connected":
                    logger.info("Already connected to server!")
                else:
                    global_monitoring_manager.reconnect(address)
        else:
            address = ((global_network_config.get_config_value("SERVER_IP"),
                        global_network_config.get_config_value("SERVER_UDP_PORT")))
            global_monitoring_manager.reconnect(address)

    @ExtendedController.observe("ping", after=True)
    def on_ping_received(self, model, prop_name, info):
        """
        Observes ping list in model. Refreshes connection_list_store when triggered
        :param model:
        :param prop_name:
        :param info:
        :return:
        """
        self.refresh_con()

    @ExtendedController.observe("status", after=True)
    def refresh_con(self, *args):
        """
        Observes status list in model. Refreshes connection_list_store triggered
        :param args:
        :return:
        """
        path = self.view["connection_tree_view1"].get_cursor()[0]
        self.connection_list_store.clear()
        for address in self.network_manager_model.connected_ip_port:
            ip = address[0]
            port = address[1]
            ident = self.network_manager_model.get_connected_id(address)
            ping = self.network_manager_model.get_connected_ping(address)
            status = self.network_manager_model.get_connected_status(address)
            if status == "connected":
                self.connection_list_store.append([ip, ident, port,
                                                   constants.set_icon_and_text(constants.ICON_NET, status,
                                                                               'fgcolor="#07F743"', ping)])
            elif status == "disconnected":
                self.connection_list_store.append([ip, ident, port,
                                                   constants.set_icon_and_text(constants.ICON_DISCONNECTED, status,
                                                                               'fgcolor="#e95815"', ping)])
            else:
                self.connection_list_store.append([ip, ident, port,
                                                   constants.set_icon_and_text(constants.ICON_DISABLED, status,
                                                                               'fgcolor="#d98508"', ping)])
            if path is not None:
                self.view["connection_tree_view1"].set_cursor(path)

    @ExtendedController.observe("config_list", after=True)
    def refresh_config(self, model, prop_name, info):
        """
        Observes config_list in model. Refreshes config_list_store
        :param model:
        :param prop_name:
        :param info:
        :return:
        """
        self.config_list_store.clear()
        for key in info.instance:
            self.config_list_store.append(key)

    def editing_started(self, renderer, editable, path):
        """
        Callback method to connect entry-widget focus-out-event to the respective change-method.
        """

        if self.view['value_text'] is renderer:
            self._actual_entry = (editable, editable.connect('focus-out-event', self.change_value))
        else:
            logger.error("Not registered Renderer was used")

    def editing_canceled(self, event):
        """ Callback method to disconnect entry-widget focus-out-event to the respective change-method.
        """
        if self._actual_entry is not None:
            self._actual_entry[0].disconnect(self._actual_entry[1])
            self._actual_entry = None

    def change_value(self, entry, event):
        """ Change-value-method to set the value of actual selected (row) global variable.
        """
        logger.info("change value {0}".format(event.type))
        if self.view['conf_tree_view'].get_cursor()[0] is None or \
                not self.view['conf_tree_view'].get_cursor()[0][0]:
            return
        self.on_value_changed(entry, self.view['conf_tree_view'].get_cursor()[0][0], text=entry.get_text())

    def on_value_changed(self, widget, path, text):
        """Triggered when a config value is edited.

        :param path: The path identifying the edited variable
        :param text: New variable value
        """
        if self.config_list_store[int(path)][1] == text:
            return
        key = self.config_list_store[int(path)][0]
        data_type = type(global_network_config.get_config_value(key))
        try:
            if data_type == bool:
                if text == "False":
                    value = False
                elif text == "True":
                    value = True
                else:
                    logger.info("Invalid input: {0}".format(str(text)))
                    return
            else:
                value = data_type(text)
            self.network_manager_model.set_config_value(key, value)
        except RuntimeError as e:
            logger.exception(e)

    @staticmethod
    def on_save_button_clicked(*args):
        """
        Overwrites configuration in network_monitoring_config.yaml when triggered
        :param args:
        :return:
        """
        logger.info("Saving configurations...")
        global_network_config.save_configuration()

    def on_load_button_clicked(self, *args):
        """
        Loads the recent network_monitoring_config.yaml when triggered
        :param args:
        :return:
        """
        self.network_manager_model.load_config(global_monitoring_manager.get_config_path())

    @staticmethod
    def on_apply_button_clicked(self, *args):
        """
        Reinitializes the client plugin with config.
        :param args:
        :return:
        """
        for address in self.network_manager_model.connected_ip_port:
            global_monitoring_manager.disconnect(address)
            self.network_manager_model.delete_connection(address)
        logger.info("Applying configurations...")
        global_monitoring_manager.reinitialize()

    @ExtendedController.observe("history_list", after=True)
    def update_history(self, model, prop_name, info):
        """
        Observes history_list from model. Updates history_list_store when triggered
        :param model:
        :param prop_name:
        :param info:
        :return:
        """
        self.history_list_store.clear()
        for key in info.instance:
            address, status = key
            self.history_list_store.append(["Server {0} {1} at port {2}".format(address[0], status, address[1])])

    @ExtendedController.observe("message_list", after=True)
    def update_message(self, model, prop_name, info):
        """
        Observes message_list from model. Updates message_list_store when triggered
        :param model:
        :param prop_name:
        :param info:
        :return:
        """
        self.message_list_store.clear()
        for key in info.instance:
            if key[2] == "received":
                self.message_list_store.append(["Message: {0} {1} from {2}".format(key[0], key[2], key[1])])
            elif key[2] == "send":
                self.message_list_store.append(["Message: {0} {1} to {2}".format(key[0], key[2], key[1])])

    @staticmethod
    def on_reload_button_clicked(self, *args):
        """
        Reloads history_list in model when triggered
        :param args:
        :return:
        """
        self.network_manager_model.reload_history()

    @staticmethod
    def on_clear_button_clicked(self, *args):
        """
        Clears history_list in model when triggered
        :param args:
        :return:
        """
        self.network_manager_model.clear_history()

    @staticmethod
    def on_message_reload_button_clicked(self, *args):
        """
        Reloads message_list in model when triggered
        :param args:
        :return:
        """
        self.network_manager_model.reload_message()

    @staticmethod
    def on_message_clear_button_clicked(self, *args):
        """
        Clears message_list in model when triggered
        :param args:
        :return:
        """
        self.network_manager_model.clear_message()


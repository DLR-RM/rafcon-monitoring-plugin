from gtkmvc import ModelMT
from acknowledged_udp.config import global_network_config
from rafcon.utils import log
logger = log.get_logger(__name__)


class NetworkManagerModel(ModelMT):
    status = []
    ping = []
    history_list = []
    message_list = []
    config_list = []
    __observables__ = ["status", "ping", "history_list", "message_list", "config_list", ]

    def __init__(self, status=[], ping=[], history_list=[], message_list=[], config_list=[], meta=None):
        ModelMT.__init__(self)
        self.connected_ip_port = []
        self.status = status
        self.id = []
        self.ping = ping
        self.controller = None
        self.history_list = history_list
        self.history_store_list = []
        self.message_list = message_list
        self.message_store_list = []
        self.config_list = config_list
        self.register_observer(self)

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
                       'CLIENT_ID',
                       'SERVER_ID'
                       }

    def set_connected_ip_port(self, address):
        """
        A method to set a connected port into the connected_port_ip list: [('ip', port)]
        :param address: address of client or server ('ip', port)
        :return:
        """
        if address not in self.connected_ip_port:
            self.connected_ip_port.append(address)

    def set_connected_id(self, address, ident):
        """
        A method to set the client or server ID into the id list: [(('ip', port), ident)]
        :param address: address of client or server('ip', port)
        :param ident: ID of the client or server
        :return:
        """
        if address in self.connected_ip_port:
            if not self.id:
                self.id.append((address, ident))
            else:
                for key in self.id:
                    if address == key[0]:
                        self.id.remove(key)
                        self.id.append((address, ident))
                if address not in key:
                    self.id.append((address, ident))

    def set_connected_ping(self, address, ping):
        """
        A method to set the connected server or client ping into the ping list: [(('ip', port), ping)]
        Gets triggert by ping thread
        :param address: ('ip', port)
        :param ping: 'ping'
        :return:
        """
        if not self.ping:
            self.ping.append((address, ping))
        if address in self.connected_ip_port:
            for key in self.ping:
                if address in key:
                    self.ping.remove(key)
                    self.ping.append((address, ping))
                else:
                    self.ping.append((address, ping))

    def set_connected_status(self, address, status):
        """
        A method to set the status of a connection into status list: [(('ip', port), status)]
        :param address: ('ip', port)
        :param status: status can be 'disconnected', 'connected' or 'disabled'
        :return:
        """
        if address in self.connected_ip_port:
            if not self.status:
                self.status.append((address, status))
            else:
                for key in self.status:
                    if address == key[0]:
                        self.status.remove(key)
                        self.status.append((address, status))
                if address not in key:
                    self.status.append((address, status))
        self.history_list.append((address, status))
        self.history_store_list.append((address, status))
        # self.update_view()

    def get_connected_id(self, address):
        """
        A method to get the id of an address
        :param address: ('ip', port)
        :return: id
        """
        for key, ident in self.id:
            if key == address:
                return ident

    def get_connected_ping(self, address):
        """
        A method to get the ping of an address
        :param address: ('ip', port)
        :return: ping
        """
        for key, ping in self.ping:
            if key == address:
                return ping

    def get_connected_status(self, address):
        """
        A method to get the status of an address
        :param address: ('ip', port)
        :return: status
        """
        for key, status in self.status:
            if key == address:
                return status

    def remove_connected_ip_port(self, address):
        """
        A method to remove an address from connection_ip_port list
        :param address: target address('ip', port)
        :return:
        """
        if address in self.connected_ip_port:
            self.connected_ip_port.remove(address)

    def remove_connected_id(self, address):
        """
        A method to remove an ID from id list
        :param address: target address('ip', port)
        :return:
        """
        for key in self.id:
            if address in key:
                self.id.remove(key)

    def remove_ping(self, address):
        """
        A method to remove a ping from ping list
        :param address: target address('ip', port)
        :return:
        """
        for key in self.ping:
            if address in key:
                self.ping.remove(key)

    def remove_status(self, address):
        """
        A method to remove a status from status list
        :param address: target address('ip', port)
        :return:
        """
        for key in self.status:
            if address in key:
                self.status.remove(key)

    def delete_connection(self, address):
        """
        A method to delete the hole connection. Triggert by server to remove connection from connection treeview.
        :param address: target address('ip', port)
        :return:
        """
        self.remove_connected_id(address)
        self.remove_connected_ip_port(address)
        self.remove_ping(address)
        self.remove_status(address)

    def delete_all(self):
        """
        A method to remove all connections from all lists
        :return:
        """
        del self.connected_ip_port[:]
        del self.id[:]
        del self.ping[:]
        del self.status[:]

    def clear_history(self):
        """
        A method to clear history_list. Triggert when clear_history_button in clicked.
        :return:
        """
        del self.history_list[:]

    def reload_history(self):
        """
        A method to relaod history_list. Triggert when relaod_history_button in clicked.
        :return:
        """
        self.history_list = []
        for key in self.history_store_list:
            self.history_list.append(key)

    def add_to_message_list(self, message_content, address, direction):
        """
        A method to append messages to message_list. Triggert when message send or received .
        :param message_content: 'message_content'
        :param address: ('ip', port)
        :param direction: 'send' or 'received'
        :return:
        """
        self.message_store_list.append((message_content, address, direction))
        self.message_list.append((message_content, address, direction))

    def clear_message(self):
        """
        A method to clear message_list. Triggert when clear_message_button in clicked.
        :return:
        """
        del self.message_list[:]

    def reload_message(self):
        """
        A method to relaod message_list. Triggert when reload_message_button in clicked.
        :return:
        """
        self.message_list = []
        for key in self.message_store_list:
            self.message_list.append(key)
        # self.controller.update_message(self.message_list)

    def set_config_value(self, param, value):
        """
        A method to set all config values into the config_list.
        :param param: dict with config values to search in network_monitoring_config.YAML
        :param value: new value for a config which shall be updated
        :return:
        """
        if not self.config_list:
            for key in self.params:
                if global_network_config.get_config_value(key):
                    self.config_list.append((key, global_network_config.get_config_value(key)))
        else:
            for key in self.config_list:
                if param == key[0]:
                    index = self.config_list.index(key)
                    self.config_list.remove(key)
                    global_network_config.set_config_value(param, value)
                    self.config_list.insert(index, (param, value))

    def load_config(self, path):
        """
        A method to reload the origin network_monitoring_config.YAML
        :param path: path to the config file
        :return:
        """
        global_network_config.load(path=path)
        del self.config_list[:]
        self.set_config_value(None, None)


network_manager_model = NetworkManagerModel()

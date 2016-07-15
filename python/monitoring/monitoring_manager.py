"""
.. module:: monitoring manager
   :platform: Unix, Windows
   :synopsis: A module to hold all execution monitoring functionality

.. moduleauthor:: Benno Voggenreiter


"""
from client import MonitoringClient
from server import MonitoringServer
from acknowledged_udp.config import global_network_config
from rafcon.statemachine.singleton import argument_parser

from yaml_configuration.config import config_path
import rafcon.utils.filesystem as filesystem

from rafcon.utils import log
import time
from twisted.internet import defer

logger = log.get_logger(__name__)


class MonitoringManager():
    """
    This class holds all monitoring relevant objects. It is configured via a config via given on startup or loaded
    from the default RAFCON config location.
    """

    def __init__(self):

        home_path = filesystem.get_home_path()

        argument_parser.add_argument(
            '-nc', '--net_config', action='store', type=config_path, metavar='path', dest='net_config_path',
            default=home_path, nargs='?', const=home_path,
            help="path to the configuration file net_config.yaml. Use 'None' to prevent the generation of "
                 "a config file and use the default configuration. Default: {0}".format(home_path))

        self.endpoint = None
        self.endpoint_initialized = False
        self.config = None
        self.config_flag = False

    def initialize(self, setup_config):
        """
        The is an initialization function, which is called when the connection finally is set up.
        :param setup_config: the setup configuration for the networking
        :return:
        """
        if not self.config_flag:
            self.config = setup_config
            self.config_flag = True
        if global_network_config.get_config_value("SERVER", True):
            if not self.endpoint:
                self.endpoint = MonitoringServer()
            self.endpoint_initialized = self.endpoint.connect()

        else:
            if not self.endpoint:
                self.endpoint = MonitoringClient()
            self.endpoint_initialized = self.endpoint.connect()
        return self.endpoint_initialized

    @staticmethod
    def networking_enabled():
        """
        A method to check if the monitoring capability is globally enabled.
        :return:
        """
        return global_network_config.get_config_value("ENABLED", False)

    def disconnect(self, address):
        """
        A method to disconnect client- or server address
        :param address: address('ip', port)
        :return:
        """
        self.endpoint.disconnect(address)

    def disable(self, address):
        """
        A method to en- and disable client from server
        :param address: client address ('ip', port)
        :return:
        """
        self.endpoint.disable(address)

    def reconnect(self, address):
        """
        A method to reconnect client to server
        :param address: client address ('ip', port)
        :return:
        """
        self.endpoint.reconnect(address)

    def get_config_path(self):
        """
        Function to get the config path
        :return: path to network_config.yaml
        """
        return self.config['net_config_path']

    def get_host(self):
        """
        Function to get connected hosts
        :return: connected host
        """
        return self.endpoint.get_host()

    def shutdown(self):
        """
        A method to shutdown the plugin. Triggered when shutting down Rafcon
        :return:
        """
        if self.endpoint:
            self.endpoint.shutdown()

    @defer.inlineCallbacks
    def reinitialize(self, addresses):
        """
        A method to reinitialize the plugin. Called when applying changes in config
        Disconnects all connections and connects with new config
        :return:
        """
        yield defer.maybeDeferred(self.endpoint.cut_connection, addresses)
        if self.networking_enabled():
            logger.info("Reinitializing...")
            self.endpoint = None
            yield defer.maybeDeferred(self.initialize, None)
        else:
            logger.error("Networking disabled!")


# this variable is always created when the this module is imported, this is our common way to integrate plugins
global_monitoring_manager = MonitoringManager()

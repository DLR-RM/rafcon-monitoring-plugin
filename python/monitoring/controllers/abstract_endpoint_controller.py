"""
.. module:: abstract controller
   :platform: Unix, Windows
   :synopsis: a module with the redundant functions for server and client

.. moduleauthor:: Benno Voggenreiter

"""
from monitoring.model.network_model import network_manager_model
from monitoring.monitoring_manager import global_monitoring_manager
from acknowledged_udp.config import global_network_config
from rafcon.utils import log
import time

logger = log.get_logger(__name__)


class AbstractController():
    """
    Controller handling the redundant functions for server and client
    """

    def __init__(self):
        self._actual_entry = None

    @staticmethod
    def on_load_button_clicked(self, *args):
        """
        Loads the recent network_monitoring_config.yaml when triggered
        :param args:
        :return:
        """
        network_manager_model.load_config(global_monitoring_manager.get_config_path())

    @staticmethod
    def on_history_reload_button_clicked(self, *args):
        """
        Reloads history_list in model when triggered
        :param args:
        :return:
        """
        network_manager_model.reload_history()

    @staticmethod
    def on_history_clear_button_clicked(self, *args):
        """
        Clears history_list in model when triggered
        :param args:
        :return:
        """
        network_manager_model.clear_history()

    @staticmethod
    def on_message_reload_button_clicked(self, *args):
        """
        Reloads message_list in model when triggered
        :param args:
        :return:
        """
        network_manager_model.reload_message()

    @staticmethod
    def on_message_clear_button_clicked(self, *args):
        """
        Clears message_list in model when triggered
        :param args:
        :return:
        """
        network_manager_model.clear_message()

    @staticmethod
    def on_load_button_clicked(self, *args):
        """
        Loads the recent network_monitoring_config.yaml when triggered
        :param args:
        :return:
        """
        network_manager_model.load_config(global_monitoring_manager.get_config_path())

    @staticmethod
    def on_save_button_clicked(*args):
        """
        Overwrites configuration in network_monitoring_config.yaml when triggered
        :param args:
        :return:
        """
        logger.info("Saving configurations...")
        global_network_config.save_configuration()

    @staticmethod
    def on_apply_button_clicked(*args):
        """
        Reinitialize the client plugin with config.
        :param args:
        :return:
        """
        logger.info("Applying configurations...")

        global_monitoring_manager.reinitialize(network_manager_model.connected_ip_port)

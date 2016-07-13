"""
.. module:: monitoring client
   :platform: Unix, Windows
   :synopsis: A module to care about receiving execution status from another RAFCON instance and showing it in its own
            RAFCON instance

.. moduleauthor:: Benno Voggenreiter


"""

import time
import sys
from monitoring_execution_engine import MonitoringExecutionEngine
from acknowledged_udp.udp_client import UdpClient
from acknowledged_udp.protocol import Protocol, MessageType
from acknowledged_udp.config import global_network_config
from rafcon.statemachine.singleton import state_machine_manager, state_machine_execution_engine
from rafcon.statemachine.enums import StateExecutionState
import rafcon
from monitoring.model.network_model import network_manager_model
from rafcon.utils import log

from threading import Thread
from monitoring.ping_endpoint import ping_endpoint

logger = log.get_logger(__name__)


class MonitoringClient(UdpClient):
    """
    A class to care about receiving execution status from another RAFCON instance and showing it in its own
    RAFCON instance
    """

    def __init__(self):
        UdpClient.__init__(self)
        self.udp = UdpClient()
        self.connector = None
        self.server_address = None
        self.datagram_received_function = self.monitoring_data_received_function
        self.execution_engine_replaced = False
        self.registered_to_execution_engine = False
        self.connector_created = False
        self.registered_to_server = False
        self.avoid_timeout = False
        self.disabled = False

    def connect(self):
        """
        Connect to the remote RAFCON server instance. Several things are achieved here:
        - replacing the menu bar by a menu bar controlling the remote RAFCON instance
        - registering to changes of the local execution engine
        - registering to the remote RAFCON server instance
        :return:
        """
        # replace state machine execution engine
        if not self.execution_engine_replaced:
            engine = MonitoringExecutionEngine(state_machine_manager, self)
            self.init_execution_engine(engine)

        if not self.disabled:

            if not self.registered_to_server:
                # if not self.connector_created:
                # setup twisted
                print "this version"
                from twisted.internet import reactor
                self.server_address = (global_network_config.get_config_value("SERVER_IP"),
                                       global_network_config.get_config_value("SERVER_UDP_PORT"))
                logger.info("Connect to server {0}!".format(str(self.server_address)))
                self.connector = reactor.listenUDP(0, self)
                self.connector_created = True
                logger.info("self.connector {0}".format(str(self.connector)))

                protocol = Protocol(MessageType.REGISTER,
                                    "Registering@{0}".format(global_network_config.get_config_value("CLIENT_ID")))
                logger.info("sending protocol {0}".format(str(protocol)))
                if self.avoid_timeout is False:
                    return_value = self.send_message_acknowledged(protocol, address=self.server_address, blocking=True)
                    if return_value:
                        self.registered_to_server = True
                        self.avoid_timeout = True
                        logger.info("Initialized")
                        return True
                    else:
                        logger.error("Connection to server {0} timeout".format(str(self.server_address)))
                        sleep_time = global_network_config.get_config_value("MAX_TIME_WAITING_BETWEEN_CONNECTION_TRY_OUTS")
                        logger.info("Waiting for MAX_TIME_WAITING_BETWEEN_CONNECTION_TRY_OUTS={0} seconds!".format(str(sleep_time)))
                        time.sleep(float(sleep_time))
                        return False
                else:
                    self.send_message_non_acknowledged(protocol, address=self.server_address)

                network_manager_model.add_to_message_list('Connecting', self.server_address, "send")
            else:
                logger.info("Already connected to server!")
        else:
            logger.info("Cannot connect to server: Client disabled!")

    def monitoring_data_received_function(self, message, address):
        """
        A function that orchestrates and processes the received messages
        :param message: the received message
        :param address: the address where the message originates
        :return:
        """
        assert isinstance(message, Protocol)
        network_manager_model.add_to_message_list(message, address, "received")

        if message.message_type is MessageType.ID:
            # if address not in network_manager_model.connected_ip_port:
            network_manager_model.set_connected_ip_port(address)
            network_manager_model.set_connected_id(address, message.message_content)
            network_manager_model.set_connected_status(address, "connected")
            thread = Thread(target=ping_endpoint, args=(address, ))
            thread.daemon = True
            thread.start()

        if not self.disabled:
            if message.message_type is MessageType.STATE_ID:
                (state_path, execution_status) = message.message_content.split("@")
                state_execution_status = StateExecutionState(int(execution_status))
                # logger.info("Received state_id {0}".format(str(state_path)))
                # logger.info("Received execution_status {0} {1}".format(str(execution_status),
                #                                                        str(state_execution_status)))
                current_state = state_machine_manager.get_active_state_machine().get_state_by_path(state_path)
                current_state.state_execution_status = state_execution_status
            if message.message_type is MessageType.UNREGISTER:
                if network_manager_model.get_connected_status(address) is not "disconnected":
                    logger.info("Disconnected by {0}".format(global_network_config.get_config_value("SERVER_IP")))
                    network_manager_model.set_connected_status(address, "disconnected")
                    self.registered_to_server = False
                    self.disabled = False
                    self.connector.stopListening()
                    self.set_on_local_control()
                    # self.avoid_timeout = False
            if message.message_type is MessageType.DISABLE:
                    logger.info("Disabled monitoring by {0}".format(global_network_config.get_config_value("SERVER_IP")))
                    network_manager_model.set_connected_status(address, "disabled")
                    self.disabled = True
                    self.set_on_local_control()
        elif self.disabled:
            if message.message_type is MessageType.DISABLE:
                logger.info("Enabled monitoring by {0}".format(global_network_config.get_config_value("SERVER_IP")))
                network_manager_model.set_connected_status(address, "connected")
                self.disabled = False
                self.init_execution_engine(MonitoringExecutionEngine(state_machine_manager, self))
            elif message.message_type is MessageType.UNREGISTER:
                logger.info("Disconnected by {0}".format(global_network_config.get_config_value("SERVER_IP")))
                network_manager_model.set_connected_status(address, "disconnected")
                self.registered_to_server = False
                self.disabled = False
                self.connector.stopListening()

    def disconnect(self, address):
        """
        A function to disconnect client from server.
        :param address: client address which shall be disconnected
        :return:
        """
        if network_manager_model.get_connected_status(address) is not "disconnected":
            protocol = Protocol(MessageType.UNREGISTER, "Disconnecting")
            logger.info("sending protocol {0}".format(str(protocol)))
            self.send_message_non_acknowledged(protocol, address=address)
            # self.stopProtocol()
            self.connector.stopListening()
            # self.connector.connectionLost(reason=None)
            self.disabled = False
            # self.avoid_timeout = False
            self.registered_to_server = False
            network_manager_model.set_connected_status(address, "disconnected")
            logger.info("Disconnected from Server")
            network_manager_model.add_to_message_list("Disconnecting", address, 'send')
            self.set_on_local_control()
        else:
            logger.info("No Server connected")

    def shutdown(self):
        """
        A function to log off clients when shutting down Rafcon
        :return:
        """
        protocol = Protocol(MessageType.UNREGISTER, "Disconnecting")
        ack = self.send_message_non_acknowledged(protocol, self.server_address)
        # self.stopProtocol()

    def set_on_local_control(self):
        """
        A function to replace the monitoring_execution_engine by the state_machine_execution_engine.
        Triggered when disconnecting or disabling.
        :return:
        """
        self.registered_to_server = False
        self.execution_engine_replaced = False
        engine = state_machine_execution_engine
        self.init_execution_engine(engine)

    def reconnect(self, address):
        """
        A function to reconnect the client to the server
        :param address: client address ('ip', port)
        :return:
        """

        self.execution_engine_replaced = False
        self.connect()

    def init_execution_engine(self, engine):
        """
        A function to set the execution engine. Triggered by set_on_local_control() and connect()
        :param engine: target execution engine
        :return:
        """

        monitoring_execution_engine = engine
        # global replacement
        # TODO: modules that have already imported the singleton.state_machine_execution_engine
        # still have their old reference!!!
        rafcon.statemachine.singleton.state_machine_execution_engine = monitoring_execution_engine

        if 'rafcon.mvc' in sys.modules:
            from rafcon.mvc.singleton import main_window_controller
            # wait until the main window controller registered its view
            while not main_window_controller.get_controller("menu_bar_controller").registered_view:
                time.sleep(0.1)

            from rafcon.mvc.models.state_machine_execution_engine import StateMachineExecutionEngineModel
            rafcon.mvc.singleton.state_machine_execution_manager_model = \
                StateMachineExecutionEngineModel(rafcon.statemachine.singleton.state_machine_execution_engine)
            main_window_controller.switch_state_machine_execution_engine(
                rafcon.mvc.singleton.state_machine_execution_manager_model)
            logger.info("state machine execution engine replaced")

            # replacement for main_window_controller_only
            from rafcon.mvc.singleton import main_window_controller
            main_window_controller.get_controller("menu_bar_controller").state_machine_execution_engine = \
                monitoring_execution_engine
        self.execution_engine_replaced = True

    def cut_connection(self):
        """
        Called when reinitializing the connection.
        :return:
        """
        self.execution_engine_replaced = False
        # self.avoid_timeout = False
        # self.stopProtocol()

    def get_host(self):
        """
        Function to get connected hosts
        :return: connected hosts
        """
        return self.connector.getHost()







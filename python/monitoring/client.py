import time
import sys
from twisted.internet import defer
from threading import Thread

from monitoring_execution_engine import MonitoringExecutionEngine
from acknowledged_udp.udp_client import UdpClient
from acknowledged_udp.protocol import Protocol, MessageType
from acknowledged_udp.config import global_network_config

import rafcon
from rafcon.core.singleton import state_machine_manager, state_machine_execution_engine
from rafcon.core.states.state import StateExecutionStatus
from rafcon.gui.singleton import state_machine_manager_model
from rafcon.utils import log

from monitoring.model.network_model import network_manager_model
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
        self.registered_to_server = False
        self.disabled = False
        self.last_active_state_machine = None

    @defer.inlineCallbacks
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
            logger.info("Setting execution engine to remote...")
            engine = MonitoringExecutionEngine(state_machine_manager, self)
            self.init_execution_engine(engine)

        if not self.disabled:

            if not self.registered_to_server:
                # setup twisted
                from twisted.internet import reactor, threads
                self.server_address = (global_network_config.get_config_value("SERVER_IP"),
                                       global_network_config.get_config_value("SERVER_UDP_PORT"))
                logger.info("Connect to server {0} ...".format(str(self.server_address)))
                self.connector = reactor.listenUDP(0, self)
                # logger.info("self.connector {0}".format(str(self.connector)))
                protocol = Protocol(MessageType.REGISTER,
                                    "Registering@{0}".format(global_network_config.get_config_value("CLIENT_ID")))
                # logger.info("sending protocol {0}".format(str(protocol)))
                return_value = yield threads.deferToThread(self.send_message_acknowledged,
                                                           protocol, address=self.server_address, blocking=True)
                if return_value:
                    self.registered_to_server = True
                    logger.info("Connected!")
                    network_manager_model.add_to_message_list('Connecting', self.server_address, "send")
                    defer.returnValue(return_value)
                else:
                    logger.error("Connection to server {0} timeout".format(str(self.server_address)))
                    sleep_time = global_network_config.get_config_value("MAX_TIME_WAITING_BETWEEN_CONNECTION_TRY_OUTS")
                    logger.info("Waiting for MAX_TIME_WAITING_BETWEEN_CONNECTION_TRY_OUTS={0} seconds!".format(str(sleep_time)))
                    time.sleep(float(sleep_time))
                    self.connect()
                    defer.returnValue(return_value)
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
            network_manager_model.set_connected_ip_port(address)
            network_manager_model.set_connected_id(address, message.message_content)
            network_manager_model.set_connected_status(address, "connected")
            thread = Thread(target=ping_endpoint, args=(address, ))
            thread.daemon = True
            thread.start()

        if not self.disabled:
            if message.message_type is MessageType.STATE_ID:
                (state_path, execution_status) = message.message_content.split("@")
                state_execution_status = StateExecutionStatus(int(execution_status))
                active_state_machine = state_machine_manager.get_active_state_machine()
                if not active_state_machine:
                    active_state_machine = state_machine_manager_model.get_selected_state_machine_model().state_machine
                if active_state_machine:
                    current_state = active_state_machine.get_state_by_path(state_path)
                    current_state.state_execution_status = state_execution_status
                    self.last_active_state_machine = active_state_machine
                elif self.last_active_state_machine:
                    current_state = self.last_active_state_machine.get_state_by_path(state_path)
                    current_state.state_execution_status = state_execution_status
            if message.message_type is MessageType.UNREGISTER:
                if network_manager_model.get_connected_status(address) is not "disconnected":
                    logger.info("Disconnected by {0}".format(global_network_config.get_config_value("SERVER_IP")))
                    network_manager_model.set_connected_status(address, "disconnected")
                    self.registered_to_server = False
                    self.disabled = False
                    self.connector.stopListening()
                    self.set_on_local_control()
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

    @defer.inlineCallbacks
    def disconnect(self, address):
        """
        A function to disconnect client from server.
        :param address: client address which shall be disconnected
        :return:
        """
        logger.info("Disconnect from server: {0} ...".format(address))
        if network_manager_model.get_connected_status(address) is not "disconnected":
            protocol = Protocol(MessageType.UNREGISTER, "Disconnecting")
            # logger.info("sending protocol {0}".format(str(protocol)))
            from twisted.internet import reactor, threads
            yield threads.deferToThread(self.send_message_acknowledged, protocol, address=address, blocking=True)
            yield defer.maybeDeferred(self.connector.stopListening)
            self.disabled = False
            network_manager_model.set_connected_status(address, "disconnected")
            logger.info("Disconnected from Server!")
            network_manager_model.add_to_message_list("Disconnecting", address, 'send')
            yield defer.maybeDeferred(self.set_on_local_control)
            self.registered_to_server = False
        else:
            logger.info("No Server connected")
        defer.returnValue(True)

    def shutdown(self):
        """
        A function to log off clients when shutting down Rafcon
        :return:
        """
        protocol = Protocol(MessageType.UNREGISTER, "Disconnecting")
        self.send_message_non_acknowledged(protocol, self.server_address)

    def set_on_local_control(self):
        """
        A function to replace the monitoring_execution_engine by the execution_engine.
        Triggered when disconnecting or disabling.
        :return:
        """
        logger.info("Setting execution engine to local...")
        self.registered_to_server = False
        self.execution_engine_replaced = False
        engine = state_machine_execution_engine
        self.init_execution_engine(engine)
        return True

    @defer.inlineCallbacks
    def reconnect(self, address):
        """
        A function to reconnect the client to the server
        :param address: client address ('ip', port)
        :return:
        """
        self.execution_engine_replaced = False
        yield defer.maybeDeferred(self.connect)

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
        rafcon.core.singleton.state_machine_execution_engine = monitoring_execution_engine

        if 'rafcon.gui' in sys.modules:
            from rafcon.gui.singleton import main_window_controller
            # wait until the main window controller registered its view
            while not main_window_controller.get_controller("menu_bar_controller").registered_view:
                time.sleep(0.1)

            from rafcon.gui.models.state_machine_execution_engine import StateMachineExecutionEngineModel
            rafcon.gui.singleton.state_machine_execution_manager_model = \
                StateMachineExecutionEngineModel(rafcon.core.singleton.state_machine_execution_engine)
            main_window_controller.switch_state_machine_execution_engine(
                rafcon.gui.singleton.state_machine_execution_manager_model)
            logger.info("Execution engine replaced!")

            # replacement for main_window_controller_only
            from rafcon.gui.singleton import main_window_controller
            main_window_controller.get_controller("menu_bar_controller").state_machine_execution_engine = \
                monitoring_execution_engine
        self.execution_engine_replaced = True

    @defer.inlineCallbacks
    def cut_connection(self, addresses):
        """
        Called when reinitializing the connection. Is waiting until disconnected
        :param:
        :return:
        """
        yield defer.maybeDeferred(self.disconnect, self.server_address)
        self.execution_engine_replaced = False
        self.registered_to_server = False
        network_manager_model.delete_all()
        defer.returnValue(True)

    def get_host(self):
        """
        Function to get connected hosts
        :return: connected hosts
        """
        return self.connector.getHost()









from rafcon.core.states.container_state import ContainerState
from rafcon.core.states.library_state import LibraryState
from rafcon.core.states.state import State
from rafcon.core.singleton import state_machine_manager, state_machine_execution_engine
from rafcon.core.execution.execution_status import StateMachineExecutionStatus

from acknowledged_udp.config import global_network_config
from acknowledged_udp.protocol import Protocol, MessageType, STATE_EXECUTION_STATUS_SEPARATOR
from acknowledged_udp.udp_server import UdpServer

from monitoring.model.network_model import network_manager_model
from threading import Thread
from monitoring.ping_endpoint import ping_endpoint
from twisted.internet import threads, defer

from rafcon.utils import log
logger = log.get_logger(__name__)


class MonitoringServer(UdpServer):
    """
    This class takes care about providing execution data to remote clients. The paths of currently executed states
    are broadcasted while on the other hand execution commands form the clients are forwarded to the local
    execution engine
    """

    def __init__(self):
        UdpServer.__init__(self)
        self.connector = None
        self.initialized = False
        self.register_to_new_state_machines()
        self.register_all_statemachines()
        self.datagram_received_function = self.monitoring_data_received_function
        self.client_ip = []

    def connect(self):
        """
        This function opens a udp port for remote clients
        :return:
        """
        from twisted.internet import reactor
        self.connector = reactor.listenUDP(global_network_config.get_config_value("SERVER_UDP_PORT"), self)
        self.initialized = True
        logger.info("Initialized")
        return True

    def register_to_new_state_machines(self):
        """
        This functions registers to add_state_machine calls of the state machine manager
        :return:
        """
        state_machine_manager.add_observer(self, "add_state_machine",
                                           notify_after_function=self.on_add_state_machine_after)

    def on_add_state_machine_after(self, observable, return_value, args):
        """
        This function specifies what happens when a state machine is added to the state machine manager
        :param observable: the state machine manager
        :param return_value: the new state machine
        :param args:
        :return:
        """
        self.register_states_of_state_machine(args[1])

    def register_all_statemachines(self):
        """
        This functions registers to all state machines currently known to the state machine manager
        :return:
        """
        for id, sm in state_machine_manager.state_machines.iteritems():
            self.register_states_of_state_machine(sm)

    def register_states_of_state_machine(self, state_machine):
        """
        This functions registers all states of state machine.
        :param state_machine: the state machine to register all states of
        :return:
        """
        root = state_machine.root_state
        root.add_observer(self, "state_execution_status",
                          notify_after_function=self.on_state_execution_status_changed_after)

        self.recursively_register_child_states(root)

    def recursively_register_child_states(self, state):
        """
        A function tha registers recursively all child states of a state
        :param state:
        :return:
        """
        if isinstance(state, ContainerState):
            for state in state.states.itervalues():
                self.recursively_register_child_states(state)
                state.add_observer(self, "state_execution_status",
                                   notify_after_function=self.on_state_execution_status_changed_after)

        if isinstance(state, LibraryState):
            self.recursively_register_child_states(state.state_copy)
            state.add_observer(self, "state_execution_status",
                               notify_after_function=self.on_state_execution_status_changed_after)

    def on_state_execution_status_changed_after(self, observable, return_value, args):
        """
        This function specifies what happens if the state machine execution status of a state changes
        :param observable: the state whose execution status changed
        :param return_value: the new execution status
        :param args: a list of all arguments of the observed function
        :return:
        """
        assert isinstance(observable, State)
        message = observable.get_path() + STATE_EXECUTION_STATUS_SEPARATOR + str(observable.state_execution_status.value)
        protocol = Protocol(MessageType.STATE_ID, message)
        # if len(self.get_registered_endpoints()) == 0:
        #     logger.warn("No endpoint registered yet")
        if self.initialized:
            for address in network_manager_model.connected_ip_port:  # self.get_registered_endpoints():
                self.send_message_non_acknowledged(protocol, address)
                network_manager_model.add_to_message_list(message, address, "send")
        else:
            logger.warn("Not initialized yet")

    def monitoring_data_received_function(self, message, address):
        """
        This functions receives all messages sent by the remote RAFCON server.
        :param message: the received message
        :param address: the address (port, ip-address) of the remote server
        :return:
        """
        logger.info("Received datagram {0} from address: {1}".format(str(message), str(address)))
        assert isinstance(message, Protocol)

        network_manager_model.add_to_message_list(message.message_content, address, "received")

        if message.message_type is MessageType.REGISTER:
            ident = message.message_content.split("@")
            if 2 < ident:
                ident.append(None)
            network_manager_model.set_connected_ip_port(address)
            network_manager_model.set_connected_id(address, ident[1])
            network_manager_model.set_connected_status(address, "connected")

            if ident[1]:
                protocol = Protocol(MessageType.ID, global_network_config.get_config_value("SERVER_ID"))
                self.send_message_non_acknowledged(protocol, address)
                network_manager_model.add_to_message_list(protocol, address, "send")
            thread = Thread(target=ping_endpoint, args=(address, ))
            thread.daemon = True
            thread.start()

        elif message.message_type is MessageType.COMMAND and network_manager_model.get_connected_status(address) is not "disabled":
            received_command = message.message_content.split("@")

            execution_mode = StateMachineExecutionStatus(int(received_command[0]))

            # currently the monitoring plugin cannot select the target state machine
            sm_key, sm = state_machine_manager.state_machines.items()[0]

            if execution_mode is StateMachineExecutionStatus.STARTED:
                # as there is no dedicated RUN_TO_STATE execution status the message has to be checked for an optional
                # start state path
                if len(received_command) == 2:
                    print "start state machine from state " + received_command[1]
                    state_machine_execution_engine.start(sm.state_machine_id, start_state_path=received_command[1])
                else:
                    state_machine_execution_engine.start(sm.state_machine_id)
            elif execution_mode is StateMachineExecutionStatus.STOPPED:
                state_machine_execution_engine.stop()
            elif execution_mode is StateMachineExecutionStatus.PAUSED:
                state_machine_execution_engine.pause()
            elif execution_mode is StateMachineExecutionStatus.FORWARD_INTO:
                state_machine_execution_engine.step_into()
            elif execution_mode is StateMachineExecutionStatus.FORWARD_OVER:
                state_machine_execution_engine.step_over()
            elif execution_mode is StateMachineExecutionStatus.FORWARD_OUT:
                state_machine_execution_engine.step_out()
            elif execution_mode is StateMachineExecutionStatus.BACKWARD:
                state_machine_execution_engine.backward_step()
            elif execution_mode is StateMachineExecutionStatus.RUN_TO_SELECTED_STATE:
                state_machine_execution_engine.run_to_selected_state(received_command[1],
                                                                     state_machine_id=sm.state_machine_id)

        elif message.message_type is MessageType.UNREGISTER:
            network_manager_model.set_connected_status(address, "disconnected")
            network_manager_model.delete_connection(address)

        logger.info("Received datagram {0} from address: {1}".format(str(message), str(address)))

    def print_message(self, message, address):
        """
        A dummy function to just print a message from a certain address.
        :param message: the received message
        :param address: the origin of the message
        :return:
        """
        logger.info("Received datagram {0} from address: {1}".format(str(message), str(address)))

    @defer.inlineCallbacks
    def disconnect(self, address):
        """
        A function to disconnect client. Client will be removed from connection list
        :param address: client address which shall be disconnected
        :return:
        """
        protocol = Protocol(MessageType.UNREGISTER, "Disconnecting")
        logger.info("sending protocol {0}".format(str(protocol)))
        yield threads.deferToThread(self.send_message_acknowledged, protocol, address=address)
        network_manager_model.set_connected_status(address, "disconnected")
        network_manager_model.add_to_message_list("Disconnecting", address, "send")
        network_manager_model.delete_connection(address)
        defer.returnValue(True)

    @defer.inlineCallbacks
    def disable(self, address):
        """
        A function to dis - and enable clients.
        :param address: client address which shall be dis- or enabled
        :return:
        """
        if network_manager_model.get_connected_status(address) == "disabled":
            protocol = Protocol(MessageType.DISABLE, "Enabling")
            # logger.info("sending protocol {0}".format(str(protocol)))
            yield threads.deferToThread(self.send_message_acknowledged, protocol, address=address)
            network_manager_model.set_connected_status(address, "connected")
            network_manager_model.add_to_message_list("Enabling", address, "send")
        else:
            protocol = Protocol(MessageType.DISABLE, "Disabling")
            yield threads.deferToThread(self.send_message_acknowledged, protocol, address=address)
            network_manager_model.set_connected_status(address, "disabled")
            network_manager_model.add_to_message_list("Disabling", address, "send")

    def shutdown(self):
        """
        A function to log off from clients when shutting down Rafcon
        :return:
        """
        for address in network_manager_model.connected_ip_port:
            protocol = Protocol(MessageType.UNREGISTER, "Disconnecting")
            self.send_message_non_acknowledged(protocol, address)
            network_manager_model.add_to_message_list("Shutdown", address, "send")

    @defer.inlineCallbacks
    def cut_connection(self, addresses):
        """
        Called when reinitializing the connection. Cuts all communications.
        :return:
        """
        if self.initialized is True:
            for address in addresses:
                yield defer.maybeDeferred(self.disconnect, address)
            yield defer.maybeDeferred(self.connector.stopListening)
            self.initialized = False
        defer.returnValue(True)

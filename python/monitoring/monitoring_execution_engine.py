
from rafcon.core.execution.execution_engine import ExecutionEngine
from rafcon.core.execution.execution_status import StateMachineExecutionStatus
from rafcon.core.singleton import state_machine_manager, state_machine_execution_engine
from monitoring.model.network_model import network_manager_model
from acknowledged_udp.protocol import Protocol, MessageType


from rafcon.utils import log
logger = log.get_logger(__name__)


class MonitoringExecutionEngine(ExecutionEngine):
    """
    This class inherits from the StatemachineExecutionEngine and thus can replace it. It is used by a monitoring
     client and overwrites common execution functions. The functionality of the functions to control
     the local execution engine are replaced with functions to control the remote execution engine.
    """

    def __init__(self, sm_manager, communication_endpoint):
        ExecutionEngine.__init__(self, sm_manager)
        self.communication_endpoint = communication_endpoint

    # overwrite all execution functions
    def start(self,  state_machine_id=None, start_state_path=None):
        assert state_machine_id
        if not state_machine_execution_engine.finished_or_stopped():
            # this is a resume
            self.set_execution_mode(StateMachineExecutionStatus.STARTED)
            pass
        else:
            self.set_execution_mode(StateMachineExecutionStatus.STARTED)
            # if the first call of a start is a resume (e.g. if the remote server started and paused the sm)
            # then setting the active_state_machine_id will fail as during execution it must not be changed
            # thus we use the protected setter here
            self.state_machine_manager._active_state_machine_id = state_machine_id
            if start_state_path:
                logger.info("Starting state machine on remote server from path {0} ...".format(start_state_path))
                protocol = Protocol(MessageType.COMMAND, str(self.status.execution_mode.value) + "@" + start_state_path)
                self.send_current_execution_mode(protocol)
            else:
                logger.info("Starting state machine on remote server ...")
                self.send_current_execution_mode()

    def pause(self):
        self.set_execution_mode(StateMachineExecutionStatus.PAUSED)
        logger.info("Pausing state machine on remote server ...")
        self.send_current_execution_mode()

    def stop(self):
        self.set_execution_mode(StateMachineExecutionStatus.STOPPED)
        logger.info("Stopping state machine on remote server ...")
        self.send_current_execution_mode()
        self.state_machine_manager.active_state_machine_id = None

    def step_mode(self, state_machine_id=None):
        assert state_machine_id
        self.state_machine_manager.active_state_machine_id = state_machine_id
        # selecting another state_machine is not supported yet!
        self.set_execution_mode(StateMachineExecutionStatus.FORWARD_INTO)
        logger.info("Step mode activated on remote server ...")
        self.send_current_execution_mode()

    def step_into(self):
        self.set_execution_mode(StateMachineExecutionStatus.FORWARD_INTO)
        logger.info("Step into on remote server ...")
        self.send_current_execution_mode()

    def step_over(self):
        self.set_execution_mode(StateMachineExecutionStatus.FORWARD_OVER)
        logger.info("Step over on remote server ...")
        self.send_current_execution_mode()

    def step_out(self):
        self.set_execution_mode(StateMachineExecutionStatus.FORWARD_OUT)
        logger.info("Step out on remote server ...")
        self.send_current_execution_mode()

    def backward_step(self):
        self.set_execution_mode(StateMachineExecutionStatus.BACKWARD)
        logger.info("Step backward on remote server ...")
        self.send_current_execution_mode()

    def run_to_selected_state(self, path, state_machine_id=None):
        assert state_machine_id
        logger.info("Run to selected state on remote server ...")
        self.state_machine_manager.active_state_machine_id = state_machine_id
        self.run_to_states = []
        self.run_to_states.append(path)
        self.set_execution_mode(StateMachineExecutionStatus.RUN_TO_SELECTED_STATE)
        protocol = Protocol(MessageType.COMMAND, str(self.status.execution_mode.value) + "@" + self.run_to_states[0])
        self.send_current_execution_mode(protocol)
        network_manager_model.add_to_message_list(str(self.status.execution_mode.value) + "@" + self.run_to_states[0],
                                                  self.communication_endpoint.server_address, "send")

    def send_current_execution_mode(self, protocol=None):
        """
        This function sends the current execution engine status to the connected remote server
        :return:
        """
        if protocol:
            self.communication_endpoint.send_message_non_acknowledged(protocol, self.communication_endpoint.server_address)
        else:
            protocol = Protocol(MessageType.COMMAND, str(self.status.execution_mode.value))
            self.communication_endpoint.send_message_non_acknowledged(protocol, self.communication_endpoint.server_address)
            network_manager_model.add_to_message_list(str(self.status.execution_mode.value),
                                                      self.communication_endpoint.server_address, "send")
        # logger.info("The current execution mode is going to be sent: {0}".format(protocol))


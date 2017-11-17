
import sys
from twisted.internet.error import CannotListenError

from monitoring_manager import global_monitoring_manager
from acknowledged_udp.config import global_network_config
from rafcon.utils import log
logger = log.get_logger(__name__)


def pre_init():
    """
    The pre_init function of the monitoring plugin. Currently nothing has to be done here
    :return:
    """
    logger.info("Nothing to do in the pre init phase of the monitoring plugin")


def post_init(setup_config):
    """
    The post_init function of the monitoring plugin. If networking is enabled the global monitoring manager is tried
    to be initialized = setting up a network connection to another endpoint
    :param setup_config:
    :return:
    """
    logger.info("Running post init of the monitoring plugin")

    global_network_config.load(path=setup_config['net_config_path'])

    if global_monitoring_manager.networking_enabled():

        def initialize_monitoring_manager():
            monitoring_manager_initialized = False
            try:
                while not monitoring_manager_initialized:
                    logger.info("Try to initialize the global monitoring manager and setup the connection to the server!")
                    succeeded = global_monitoring_manager.initialize(setup_config)
                    if succeeded:
                        monitoring_manager_initialized = True
            except CannotListenError, e:
                logger.exception("Cannot start rafcon as a server: Address already in use!")

        import threading
        init_thread = threading.Thread(target=initialize_monitoring_manager)
        init_thread.daemon = True
        init_thread.start()

    if not global_network_config.get_config_value("SERVER") and not 'rafcon.gui' in sys.modules:
        logger.error("Starting RAFCON with the monitoring plugin in client mode without GUI, does not make sense ...")


def main_window_setup(main_window_controller):
    """
    Launches the model-view-controller of monitoring plugin. Called in controllers/main_window.py
    :param main_window_controller:
    :return:
    """
    from monitoring.views.server_connection import ServerView
    from monitoring.views.client_connection import ClientView
    from monitoring.controllers.server_controller import ServerController
    from monitoring.controllers.client_controller import ClientController
    from monitoring.model.network_model import network_manager_model
    from rafcon.gui.helpers.label import create_tab_header_label
    import constants

    icon = {"network": constants.ICON_NET}
    monitoring_plugin_eventbox = create_tab_header_label("network", icon)

    if global_network_config.get_config_value("SERVER"):
        main_window_controller.view.state_machine_server = ServerView()
        main_window_controller.view.state_machine_server.show()
        main_window_controller.view['lower_notebook'].append_page(main_window_controller.view.state_machine_server.get_top_widget(),
                                                                  monitoring_plugin_eventbox)
        monitoring_manager_ctrl = ServerController(network_manager_model, main_window_controller.view.state_machine_server)
    else:
        main_window_controller.view.state_machine_client = ClientView()
        main_window_controller.view.state_machine_client.show()
        main_window_controller.view['lower_notebook'].append_page(main_window_controller.view.state_machine_client.get_top_widget(),
                                                                  monitoring_plugin_eventbox)
        monitoring_manager_ctrl = ClientController(network_manager_model, main_window_controller.view.state_machine_client)
    main_window_controller.add_controller('monitoring_manager_ctrl', monitoring_manager_ctrl)


def pre_destruction():
    """
    Triggered when shutting down main_window_controller. Clean shutdown of the plugin
    :param:
    :return:
    """
    global_monitoring_manager.shutdown()

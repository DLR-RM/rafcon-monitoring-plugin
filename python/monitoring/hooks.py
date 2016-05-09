"""
.. module:: hooks
   :platform: Unix, Windows
   :synopsis: This is the hook module for the monitoring plugin.

.. moduleauthor:: Sebastian Brunner


"""


from monitoring_manager import global_monitoring_manager
from acknowledged_udp.config import global_network_config
from twisted.internet.error import CannotListenError
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



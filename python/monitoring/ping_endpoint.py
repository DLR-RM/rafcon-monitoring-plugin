
import subprocess
from monitoring.model.network_model import network_manager_model


def ping_endpoint(address):
    """
    A function to get the ping of the client or server address.
    Tries to ping address 5 times and sets the average time into model
    :param address: ('ip', port)
    :return:
    """
    while 1:
        ping = subprocess.check_output("ping -c 5 %s | grep ' = '" % address[0], shell=True)
        times = ping.split('/')
        network_manager_model.set_connected_ping(address, times[4])


# if __name__ == '__main__':
#     pinger(('8.8.8.8', 9999))

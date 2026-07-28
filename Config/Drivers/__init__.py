#%% Importing Config Tools
from .Phase0 import Phase0
#%% Importing Config Packets
class Drivers:
    class Phases:
        Phase0 = Phase0
    class General:
        Activation = True
        Version = 0
        Debug = False
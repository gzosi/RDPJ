#%% Importing Config Tools
from .Phase0 import Phase0
from .Phase1 import Phase1
#%% Importing Config Packets
class Drivers:
    class Phases:
        Phase0 = Phase0
        Phase1 = Phase1
    class General:
        Activation = True
        Version = 0
        Debug = False
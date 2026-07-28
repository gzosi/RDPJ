#%% Importing Libreries
import os
#%% Importing Config Packets
from .Drivers import Drivers
from .Media import Media
#%% Defining Config Class
class Config:
    class Settings:
        class CaseStudy:
            Fov = 'Fov1'
            Kt = 'Kt1'
            Sigma = 'Sigma1'
        class Acquisition:
            pass
    class Packages:
        Drivers = Drivers
        Media = Media
    class Paths:
        mainRooot = os.getcwd()
        class CodeRoots:
            DriversRoot = 'Drivers'
            MediaRoot = 'Media'
            ConfigRoot = 'Config'
        class DataRoots:
            ResourcesRoot = 'Resources'
            RawDataRoot = 'RawData'
            StreamRoot = 'IOStream'
            DependeciesRoot = 'Dependencies'
            @staticmethod
            def CaseStudyRoot():
                cs = Config.Settings.CaseStudy
                return os.path.join(cs.Prop, cs.Pov, cs.Kt, cs.Sigma)
    class General:
        Version = 0
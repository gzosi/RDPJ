#%% Importing Libreries
import cv2 as cv
#%% Defining Config Packet
class Task1:
    class MetaData:
        InputExt = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        OutputName = 'Data.h5'
    class Settings:
        class Rotation:
            Fov1 = None
    class General:
        Activation = True
        Maker = True
        Destroyer = False
        Version = 0
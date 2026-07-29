#%% Defining Config Packet
class Task1:
    class MetaData:
        OutputName = 'Data.h5'
    class Settings:
        class SpaceTime:
            mm_per_pixel = 0.05316
            dt_seconds = 7e-5
        class Piv:
            tile_size = 1024
            overlap = 128
    class General:
        Activation = False
        Maker = True
        Destroyer = False
        Version = 0
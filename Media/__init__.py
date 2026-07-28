#%% Importing Libreries
from termcolor import colored
#%% Importing Code Phases
# from Media import Phase0
#%% Defining Main Function
def main(Config):
    print('----------------------------------')
    print('----------------------------------')
    if Config.Packages.Media.General.Activation is True:
        print('. Media:', colored( 'Running ℹ️ ', 'cyan'))
        # print('----------------------------------')
        # Phase0.main(Config)
        # print('----------------------------------')
        print('. Media:', colored( 'Exexuted ✅', 'green'))
    elif Config.Packages.Media.General.Activation is False:
        print('. Media:',colored( 'Offline ⚠️', 'yellow'))
    else:
        raise ValueError('Plesas Set the Media Switch (on/off) ❌')
    print('----------------------------------')
    print('----------------------------------')
    return
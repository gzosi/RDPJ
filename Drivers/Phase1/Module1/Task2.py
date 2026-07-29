#%% Importing Libreries
import h5py
import numpy as np
from tqdm.auto import tqdm
from termcolor import colored
from pathlib import Path
#%% Defining Subroutines
def computeMeanFields(group1, group2, out_group, Config):
    """Calcola la media temporale di U, V e della Magnitudo in modo cumulativo per risparmiare RAM."""
    base_keys_1 = {k.rsplit('_', 1)[0] for k in group1.keys()}
    base_keys_2 = {k.rsplit('_', 1)[0] for k in group2.keys()}
    common_keys = sorted(base_keys_1 & base_keys_2)
    n_frames = len(common_keys)
    if n_frames == 0:
        return
    sum_u = None
    sum_v = None
    sum_mag = None
    for key in tqdm(common_keys, desc='Task2 Computing Means', leave=False):
        u_mms = group1[f"{key}_u"][()]
        v_mms = group2[f"{key}_v"][()]
        mag = np.sqrt(u_mms**2 + v_mms**2)
        if sum_u is None:
            sum_u = np.zeros_like(u_mms, dtype=np.float64)
            sum_v = np.zeros_like(v_mms, dtype=np.float64)
            sum_mag = np.zeros_like(mag, dtype=np.float64)
        sum_u += u_mms
        sum_v += v_mms
        sum_mag += mag
    mean_u = sum_u / n_frames
    mean_v = sum_v / n_frames
    mean_mag = sum_mag / n_frames
    out_group.create_dataset("mean_u", data=mean_u)
    out_group.create_dataset("mean_v", data=mean_v)
    out_group.create_dataset("mean_mag", data=mean_mag)
def exploreStructure(src_node, dst_node, Config):
    """Esplora e replica ricorsivamente l'albero HDF5, intercettando i dati del Task1."""
    subgroups = [name for name, obj in src_node.items() if isinstance(obj, h5py.Group)]
    if "Processed_1" in subgroups and "Processed_2" in subgroups:
        out_g = dst_node.create_group("Mean_Fields")
        computeMeanFields(src_node["Processed_1"], src_node["Processed_2"], out_g, Config)
    else:
        for name, item in src_node.items():
            if isinstance(item, h5py.Group):
                new_dst_group = dst_node.create_group(name)
                exploreStructure(item, new_dst_group, Config)
            else:
                src_node.copy(name, dst_node)
#%% Defining Main Function
def main(Config):
    if Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task2.General.Activation is True:
        print('.... Task2:', colored('Running ℹ️', 'cyan'))
        main_root = Path(Config.Paths.mainRooot)
        srcRoot = (main_root /
            Config.Paths.DataRoots.ResourcesRoot /
            Config.Paths.DataRoots.StreamRoot /
            Config.Paths.DataRoots.CaseStudyRoot() /
            Config.Packages.Drivers.__name__ / 
            Config.Packages.Drivers.Phases.Phase1.__name__ /
            Config.Packages.Drivers.Phases.Phase1.Modules.Module1.__name__ /
            Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.__name__ / 
            Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.MetaData.OutputName)
        dstRoot = (main_root /
            Config.Paths.DataRoots.ResourcesRoot /
            Config.Paths.DataRoots.StreamRoot /
            Config.Paths.DataRoots.CaseStudyRoot() /
            Config.Packages.Drivers.__name__ / 
            Config.Packages.Drivers.Phases.Phase1.__name__ /
            Config.Packages.Drivers.Phases.Phase1.Modules.Module1.__name__ /
            Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task2.__name__ /  
            Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task2.MetaData.OutputName)
        with h5py.File(srcRoot, 'r') as f_src, h5py.File(dstRoot, 'w') as f_dst:
            exploreStructure(f_src, f_dst, Config)
    elif Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task2.General.Activation is False:
        print('.... Task2:', colored('Offline ⚠️', 'yellow'))
    else:
        raise ValueError('Please Set the Task2 Switch (on/off) ❌')
    return
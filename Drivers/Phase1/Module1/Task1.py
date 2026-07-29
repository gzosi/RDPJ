#%% Importing Libreries
import h5py
import torch
import numpy as np
import torch.nn.functional as F_nn
from torchvision.models.optical_flow import raft_large, Raft_Large_Weights
from tqdm.auto import tqdm
from termcolor import colored
from pathlib import Path
#%% Defining Subroutines
def dataForRaft(img_np, device):
    """Normalizza e prepara i dati per il modello RAFT."""
    if len(img_np.shape) == 2:
        img_np = np.stack((img_np,)*3, axis=-1)
    elif len(img_np.shape) == 3 and img_np.shape[2] == 1:
        img_np = np.concatenate((img_np,)*3, axis=-1)
    t = torch.from_numpy(img_np).permute(2, 0, 1).float()
    t = (t / 255.0) * 2.0 - 1.0
    return t.unsqueeze(0).to(device)
def computeFlow(t1, t2, model, device, Config):
    """Calcola l'Optical Flow usando il tiling per gestire la memoria VRAM."""
    tile_size =  Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.Settings.Piv.tile_size
    overlap =  Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.Settings.Piv.overlap
    _, _, h, w = t1.shape
    final_flow = torch.zeros((2, h, w), dtype=torch.float32)
    weight_map = torch.zeros((2, h, w), dtype=torch.float32)
    stride = tile_size - overlap
    y_starts = list(range(0, h - tile_size, stride)) + [h - tile_size] if h > tile_size else [0]
    x_starts = list(range(0, w - tile_size, stride)) + [w - tile_size] if w > tile_size else [0]
    if h > tile_size or w > tile_size:
        win_y = torch.hann_window(tile_size).view(-1, 1).repeat(1, tile_size)
        win_x = torch.hann_window(tile_size).view(1, -1).repeat(tile_size, 1)
        blend_mask = (win_y * win_x).unsqueeze(0).repeat(2, 1, 1).cpu()
    else:
        blend_mask = torch.ones((2, h, w))
    with torch.no_grad():
        with torch.autocast(device_type=device, dtype=torch.float16):
            for y in y_starts:
                for x in x_starts:
                    tile_h, tile_w = min(tile_size, h - y), min(tile_size, w - x)
                    t1_tile = t1[:, :, y:y+tile_size, x:x+tile_size]
                    t2_tile = t2[:, :, y:y+tile_size, x:x+tile_size]
                    pad_h, pad_w = (8 - (t1_tile.shape[2] % 8)) % 8, (8 - (t1_tile.shape[3] % 8)) % 8
                    if pad_h > 0 or pad_w > 0:
                        t1_tile = F_nn.pad(t1_tile, (0, pad_w, 0, pad_h), mode='replicate')
                        t2_tile = F_nn.pad(t2_tile, (0, pad_w, 0, pad_h), mode='replicate')
                    flow_preds = model(t1_tile, t2_tile)
                    tile_flow = flow_preds[-1][0].cpu()[:, :tile_h, :tile_w]
                    mask_crop = blend_mask[:, :tile_h, :tile_w]
                    final_flow[:, y:y+tile_h, x:x+tile_w] += tile_flow * mask_crop
                    weight_map[:, y:y+tile_h, x:x+tile_w] += mask_crop
                    torch.cuda.empty_cache()
    return final_flow / (weight_map + 1e-6)
def flowInference(group1, group2, out_group1, out_group2, model, device, Config):
    """Applica la PIV e salva i risultati in unità fisiche."""
    common_keys = sorted(set(group1.keys()) & set(group2.keys()))
    mm_per_pixel = Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.Settings.SpaceTime.mm_per_pixel
    dt_seconds = Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.Settings.SpaceTime.dt_seconds
    for key in tqdm(common_keys, desc='PIV Analysis', leave=False):
        img1_np = group1[key][()]
        img2_np = group2[key][()]
        flow = computeFlow(
            dataForRaft(img1_np, device),
            dataForRaft(img2_np, device),
            model, device, Config)
        u_mms = (flow[0].numpy() * mm_per_pixel) / dt_seconds
        v_mms = (flow[1].numpy() * mm_per_pixel) / dt_seconds
        out_group1.create_dataset(f"{key}_u", data=u_mms)
        out_group2.create_dataset(f"{key}_v", data=v_mms)
def exploreStructure(src_node, dst_node, model, device, Config):
    """Esplora e replica ricorsivamente l'albero HDF5."""
    subgroups = [name for name, obj in src_node.items() if isinstance(obj, h5py.Group)]
    if len(subgroups) == 2:
        out_g1 = dst_node.create_group("Processed_1")
        out_g2 = dst_node.create_group("Processed_2")
        flowInference(src_node[subgroups[0]], src_node[subgroups[1]], out_g1, out_g2, model, device, Config)
    else:
        for name, item in src_node.items():
            if isinstance(item, h5py.Group):
                new_dst_group = dst_node.create_group(name)
                exploreStructure(item, new_dst_group, model, device, Config)
            else:
                src_node.copy(name, dst_node)
#%% Defining Main Function
def main(Config):
    if Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.General.Activation is True:
        print('.... Task1:', colored('Running ℹ️', 'cyan'))
        main_root = Path(Config.Paths.mainRooot)
        srcRoot = (main_root /
            Config.Paths.DataRoots.ResourcesRoot /
            Config.Paths.DataRoots.StreamRoot /
            Config.Paths.DataRoots.CaseStudyRoot() /
            Config.Packages.Drivers.__name__ / 
            Config.Packages.Drivers.Phases.Phase0.__name__ /
            Config.Packages.Drivers.Phases.Phase0.Modules.Module2.__name__ /
            Config.Packages.Drivers.Phases.Phase0.Modules.Module2.Tasks.Task1.__name__ /
            Config.Packages.Drivers.Phases.Phase0.Modules.Module2.Tasks.Task1.MetaData.OutputName)
        dstRoot = (main_root /
            Config.Paths.DataRoots.ResourcesRoot /
            Config.Paths.DataRoots.StreamRoot /
            Config.Paths.DataRoots.CaseStudyRoot() /
            Config.Packages.Drivers.__name__ / 
            Config.Packages.Drivers.Phases.Phase1.__name__ /
            Config.Packages.Drivers.Phases.Phase1.Modules.Module1.__name__ /
            Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.__name__ /
            Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.MetaData.OutputName)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = raft_large(weights=Raft_Large_Weights.DEFAULT, progress=False).to(device)
        model.eval()
        with h5py.File(srcRoot, 'r') as f_src, h5py.File(dstRoot, 'w') as f_dst:
            exploreStructure(f_src, f_dst, model, device, Config)
    elif Config.Packages.Drivers.Phases.Phase1.Modules.Module1.Tasks.Task1.General.Activation is False:
        print('.... Task1:', colored('Offline ⚠️', 'yellow'))
    else:
        raise ValueError('Please Set the Task1 Switch (on/off) ❌')
    return
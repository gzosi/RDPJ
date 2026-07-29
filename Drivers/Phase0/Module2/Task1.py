#%% Importing Libreries
import cv2 as cv
import h5py
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
from termcolor import colored
#%% Defining Subroutines
def directoryExplorer(config, srcRootStr, dstRootStr):
    srcRoot, dstRoot = Path(srcRootStr), Path(dstRootStr)
    if not dstRoot.exists(): return print(colored(f'CRITICAL ERROR ❌: Dest path not found!\nPath: {dstRoot}', 'red'))
    taskConfig = config.Packages.Drivers.Phases.Phase0.Modules.Module2.Tasks.Task1
    inputExt, outputName = taskConfig.MetaData.InputExt, taskConfig.MetaData.OutputName
    groupedFiles = defaultdict(list)
    for ext in inputExt:
        for filePath in srcRoot.rglob(f'*{ext}'):
            relPath = filePath.relative_to(srcRoot)
            groupedFiles[relPath.parent.as_posix()].append((filePath, relPath.parts[0]))
    finalFilesToProcess = []
    for groupPath, files in groupedFiles.items():
        files.sort(key=lambda x: str(x[0]))
        finalFilesToProcess.extend([(fPath, groupPath, cam) for fPath, cam in files])
    outputRoot = dstRoot / outputName
    outputRoot.parent.mkdir(parents=True, exist_ok=True)
    groupCounters = defaultdict(int)
    with h5py.File(outputRoot, 'w') as h5file:
        for fullPath, groupPath, fovName in tqdm(finalFilesToProcess, desc="Generazione HDF5"):
            try:
                img = cv.imread(str(fullPath), cv.IMREAD_GRAYSCALE)
                if img is None: continue
                rotationAngle = getattr(taskConfig.Settings.Rotation, fovName, None)
                if rotationAngle is not None: img = cv.rotate(img, rotationAngle)
                group = h5file.require_group(groupPath)
                group.create_dataset(f"{groupCounters[groupPath]:05d}", data=img)
                groupCounters[groupPath] += 1      
            except Exception as e: print(colored(f"Errore: {e}", 'red'))
    return
#%% Defining Main Function
def main(config):
    taskConfig = config.Packages.Drivers.Phases.Phase0.Modules.Module2.Tasks.Task1
    if taskConfig.General.Activation is True:
        print('.... Task1:', colored('Running ℹ️', 'cyan'))
        mainRoot = Path(config.Paths.mainRooot)
        srcRoot = mainRoot / config.Paths.DataRoots.ResourcesRoot / config.Paths.DataRoots.RawDataRoot / config.Paths.DataRoots.CaseStudyRoot()
        dstRoot = mainRoot / config.Paths.DataRoots.ResourcesRoot / config.Paths.DataRoots.StreamRoot / config.Paths.DataRoots.CaseStudyRoot() / config.Packages.Drivers.__name__ / config.Packages.Drivers.Phases.Phase0.__name__ / config.Packages.Drivers.Phases.Phase0.Modules.Module2.__name__ / taskConfig.__name__
        directoryExplorer(config, srcRoot, dstRoot)
        print('.... Task1:', colored('Executed ✅', 'green'))
    elif taskConfig.General.Activation is False: print('.... Task1:', colored('Offline ⚠️', 'yellow'))
    else: raise ValueError('Please Set the Task1 Switch (on/off) ❌')
    return
#%% Importing Libreries
import h5py
import json
from pathlib import Path
from termcolor import colored
#%% Defining Subroutines
def exploreFile(group, settings):
    structureShapes, structureOrigins = {}, {}
    fullW, fullH = settings.FullSensorShape
    for key, item in group.items():
        if isinstance(item, h5py.Group):
            subShapes, subOrigins = exploreFile(item, settings)
            structureShapes[key], structureOrigins[key] = subShapes, subOrigins
        elif isinstance(item, h5py.Dataset):
            currentShape = item.shape
            shapeVal = [int(x) for x in currentShape]
            imgH, imgW = int(currentShape[0]), int(currentShape[1])
            originVal = [int((fullW - imgW) / 2) if imgW < fullW else 0, int((fullH - imgH) / 2) if imgH < fullH else 0] if getattr(settings, 'IncludeOrigin', False) else None
            return shapeVal, originVal
    return structureShapes, structureOrigins
#%% Defining Main Function
def main(config):
    taskConfig = config.Packages.Drivers.Phases.Phase0.Modules.Module2.Tasks.Task2
    if taskConfig.General.Activation is True:
        print('.... Task2:', colored('Running ℹ️', 'cyan'))
        mainRoot = Path(config.Paths.mainRooot)
        baseFolder = mainRoot / config.Paths.DataRoots.ResourcesRoot / config.Paths.DataRoots.StreamRoot / config.Paths.DataRoots.CaseStudyRoot() / config.Packages.Drivers.__name__ / config.Packages.Drivers.Phases.Phase0.__name__ / config.Packages.Drivers.Phases.Phase0.Modules.Module2.__name__ / taskConfig.__name__
        baseFolder.mkdir(parents=True, exist_ok=True)
        srcDir = mainRoot / config.Paths.DataRoots.ResourcesRoot / config.Paths.DataRoots.StreamRoot / config.Paths.DataRoots.CaseStudyRoot() / config.Packages.Drivers.__name__ / config.Packages.Drivers.Phases.Phase0.__name__ / config.Packages.Drivers.Phases.Phase0.Modules.Module2.__name__ / config.Packages.Drivers.Phases.Phase0.Modules.Module2.Tasks.Task1.__name__
        if not srcDir.exists(): raise FileNotFoundError(f"Source folder not found: {srcDir}")
        allShapesData, allOriginsData = {}, {}
        h5Files = list(srcDir.rglob("*.h5"))
        if not h5Files: raise FileNotFoundError(f"No .h5 files found in: {srcDir}")
        for h5Path in h5Files:
            with h5py.File(h5Path, 'r') as f:
                shapesData, originsData = exploreFile(f, taskConfig.Settings)
                allShapesData[h5Path.stem] = shapesData
                allOriginsData[h5Path.stem] = originsData
        dstShapePath = baseFolder / taskConfig.MetaData.ShapeExt
        dstOriginPath = baseFolder / taskConfig.MetaData.OriginExt
        indent = getattr(taskConfig.MetaData, 'Indent', 4)
        with open(dstShapePath, 'w') as f: json.dump(allShapesData, f, indent=indent)
        with open(dstOriginPath, 'w') as f: json.dump(allOriginsData, f, indent=indent)
        print('.... Task2:', colored('Executed ✅', 'green'))
    elif taskConfig.General.Activation is False: print('.... Task2:', colored('Offline ⚠️', 'yellow'))
    else: raise ValueError('Please Set the Task2 Switch (on/off) ❌')
    return
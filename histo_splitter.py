from ij import IJ, ImagePlus, ImageStack
from ij.io import Opener
from ij.io import FileSaver
from loci.plugins import BF
from ij.gui import WaitForUserDialog
from loci.plugins.in import ImporterOptions
from loci.formats import ImageReader
from loci.formats import MetadataTools
from ome.units import UNITS
from ij.gui import GenericDialog
from ij.plugin.frame import RoiManager
import os
import re
import time
import logging

outDirChoices = [
    "New Directory, no subfolders",
    "New Directory, keep input subfolders",
    "Within (subfolders of) input directory"]
voxel_info = str()
startTime = time.time()
imageCount = 0

gd = GenericDialog("Set HistoSplitter.py Options")
gd.addStringField("File extension to be processed", ".tif")
gd.addStringField(
    "String to identify your input images", "Wholeslide_Default_Extended")
gd.addRadioButtonGroup("Output", outDirChoices, 3, 1, outDirChoices[2])
gd.addRadioButtonGroup("Do you want to continue?", ['yes', 'no'], 2, 1, 'no')
gd.showDialog()
if gd.wasCanceled():
    exit()

fileExt = gd.getNextString()
fileID = gd.getNextString()
outDirPref = gd.getNextRadioButton()
contPref = gd.getNextRadioButton()

if not fileExt.startswith('.'):
    fileExt = '.' + fileExt

inDir = IJ.getDirectory("Choose Directory Containing Input Files")
if inDir is None:
    exit('No input directory selected!')

if outDirPref == outDirChoices[2]:
    outDir = inDir
else:
    outDir = IJ.getDirectory("Choose Directory For Output")
    if outDir is None:
        exit('No output directory selected!')
    if outDirPref == outDirChoices[1]:
        for dirpath, dirnames, filenames in os.walk(inDir):
            if any([fileExt in f for f in filenames]):
                structure = os.path.join(outDir, dirpath[len(inDir):])
                if not os.path.isdir(structure):
                    os.makedirs(structure)

logging.basicConfig(
    filename=os.path.join(outDir, "Log.txt"), filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s >> %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S')

logging.info('Start HistoSplitter script')
logging.info('Preferences')
logging.info('    Input dir: %s', inDir)
logging.info('    Output dir: %s', outDir)
logging.info('    Output format: %s', outDirPref)
logging.info('    Continue: %s', contPref)


def saveROIImage(img, out_name):
    if outDirPref == outDirChoices[0] or outDirPref == outDirChoices[2]:
        out_file = os.path.join(outDir, out_name)
        FileSaver(img).saveAsTiff(out_file)
    elif outDirPref == outDirChoices[1]:
        outSubDir = root.replace(inDir, outDir)
        out_file = os.path.join(outSubDir, out_name)
        FileSaver(img).saveAsTiff(out_file)


def SaveVoxel(outDir, voxel_info):
    with open(os.path.join(outDir, "PhysicalSize.txt"), 'w') as output:
        output.write(voxel_info)


def saveProgress(outDir, list):
    with open(os.path.join(outDir, "ProcessedFiles.txt"), 'w') as f:
        f.write('\n'.join(list))


fileList = []
for root, dirs, files in os.walk(inDir):
    for file in files:
        find = re.findall(fileID, file)
        if find and file.endswith(fileExt):
            fileList.append(os.path.join(root, file))

if contPref == 'yes':
    processedFile = IJ.getFilePath('Please select your processed file list.')
    with open(processedFile, 'r') as p:
        processedList = [line.strip() for line in p]
    fileList = (set(fileList) | set(processedList)) - set(processedList)
else:
    processedList = []


for file in fileList:
    options = ImporterOptions()
    options.setId(file)
    imps = BF.openImagePlus(options)
    for imp in imps:
        imageCount += 1
        reader = ImageReader()
        omeMeta = MetadataTools.createOMEXMLMetadata()
        reader.setMetadataStore(omeMeta)
        reader.setId(file)

        base_name = os.path.basename(file)
        base_name = base_name.replace(fileID, '')
        base_name = base_name.replace(fileExt, '')

        physSizeX = omeMeta.getPixelsPhysicalSizeX(0)
        physSizeY = omeMeta.getPixelsPhysicalSizeY(0)
        stackSizeX = omeMeta.getPixelsSizeX(0).getValue()
        stackSizeY = omeMeta.getPixelsSizeY(0).getValue()

        voxel_info += ','.join(
                [str(entry) for entry in (file,
                physSizeX.value(), physSizeY.value(),
                stackSizeX, stackSizeY)]
            ) + '\n'

        rm = RoiManager.getInstance()
        if not rm:
            rm = RoiManager()
        rm.runCommand("reset")
        imp.setRoi(1760, 1200, 1632, 1344)
        imp.flattenStack()
        imp.show()
        wait = WaitForUserDialog("Set and add ROIs, then click OK.")
        wait.show()
        if wait.escPressed():
            logging.info('Esc was pressed')
            SaveVoxel(outDir, voxel_info)
            saveProgress(outDir, processedList)
            imp.close()
            exit()

        rm = RoiManager.getInstance()
        rois = rm.getRoisAsArray()
        if not rois:
            wait = WaitForUserDialog("You need to set ROIs, then click OK.")
            wait.show()
            if wait.escPressed():
                logging.info('Esc was pressed')
                SaveVoxel(outDir, voxel_info)
                saveProgress(outDir, processedList)
                imp.close()
                exit()
            if not rois:
                logging.info('No ROIs set')
                SaveVoxel(outDir, voxel_info)
                saveProgress(outDir, processedList)
                imp.close()
                exit()

        i = 0
        for roi in rois:
            i += 1
            imp.setRoi(roi)
            crop_imp = imp.crop()
            outname = base_name + "_ROI-" + str(i) + ".tiff"
            saveROIImage(crop_imp, outname)

        out_roi_zip_file = os.path.join(root, file.replace(fileExt, "") + "ROIs.zip")
        rm.runCommand("Save", out_roi_zip_file)
        processedList.append(file)
        imp.close()

SaveVoxel(outDir, voxel_info)
saveProgress(outDir, processedList)

duration = time.time() - startTime
logging.info('Processing finished')

duration_h, rest = divmod(duration, 3600)
duration_min, rest = divmod(rest, 60)
duration_s = int(round(rest))
if duration_h > 0:
    logging.info(
        '%i files procced in %i h, %i min and %i s',
        imageCount, duration_h, duration_min, duration_s)
elif duration_min > 0:
    logging.info(
        '%i files procced in %i min and %i s',
        imageCount, duration_min, duration_s)
else:
    logging.info('%i files procced in %i s', imageCount, duration_s)

IJ.log("\\Clear")
IJ.log("Finished")

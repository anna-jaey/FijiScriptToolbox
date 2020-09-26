import os
import re
import time
import logging
from ij import IJ, ImagePlus, ImageStack, WindowManager
from ij.io import FileSaver
from ij.plugin import ZProjector
from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from loci.formats import ImageReader, MetadataTools
from ij.gui import GenericDialog

startTime = time.time()
imageCount = 0
voxel_info = str()
channelSubfolderChoices = ["yes", "no"]

gd = GenericDialog("Set split_channels.py Options")
gd.addStringField("File extension to be processed", ".nd2")
gd.addRadioButtonGroup("Save channels in different subfolders", channelSubfolderChoices, 1, 1,
                       channelSubfolderChoices[0])
gd.addCheckbox("Voxel size", True)
gd.showDialog()
if gd.wasCanceled():
    exit()

fileExt = gd.getNextString()
channelSubfolderPref = gd.getNextRadioButton()
voxelPref = gd.getNextBoolean()

inDir = IJ.getDirectory("Choose Directory Containing Input Files (" + str(fileExt) + ')')
outDir = IJ.getDirectory("Choose Directory For Output")

logging.basicConfig(filename=os.path.join(outDir, "Log.txt"), filemode='w', level=logging.DEBUG,
                    format='%(asctime)s | %(levelname)s >> %(message)s', datefmt='%Y/%m/%d %H:%M:%S')

logging.info('Start split_channels script')
logging.info('Preferences')
logging.info('    Input dir: %s', inDir)
logging.info('    Output dir: %s', outDir)
logging.info('    processed files format: %s', fileExt)
logging.info('    Save channels in different subfolders: %s', channelSubfolderPref)


def saveImage(img, out_file):
    FileSaver(img).saveAsTiff(out_file)


for root, dirs, files in os.walk(inDir):
    for file in files:
        if file.endswith(fileExt):
            logging.info('Starting image #%i (%s)', imageCount, str(file))
            options = ImporterOptions()
            options.setAutoscale(True)
            options.setId(os.path.join(root, file))
            options.setSplitChannels(True)
            imps = BF.openImagePlus(options)
            for imp in imps:
                reader = ImageReader()
                omeMeta = MetadataTools.createOMEXMLMetadata()
                reader.setMetadataStore(omeMeta)
                reader.setId(os.path.join(root, file))

                filename = str(imp)
                channel_id = int(re.findall("C=(\d)", filename)[0])
                channel_name = omeMeta.getChannelName(0, channel_id)
                out_name = filename.split('"')[1]
                out_name = out_name.split(fileExt)[0] + "_" + str(channel_name)
                out_name = out_name.replace(" ", "")

                physSizeX = omeMeta.getPixelsPhysicalSizeX(0)
                physSizeY = omeMeta.getPixelsPhysicalSizeY(0)
                physSizeZ = omeMeta.getPixelsPhysicalSizeZ(0)
                stackSizeX = omeMeta.getPixelsSizeX(0).getValue()
                stackSizeY = omeMeta.getPixelsSizeY(0).getValue()
                stackSizeZ = omeMeta.getPixelsSizeZ(0).getValue()
                logging.info('    Saving under: %s', out_name)
                logging.info('        Size in micrometer: %.4f, %.4f, %.4f', physSizeX.value(), physSizeY.value(), physSizeZ.value())
                logging.info('        Size in pixel: %i, %i, %i', stackSizeX, stackSizeY, stackSizeZ)
                voxel_info += ','.join([str(entry) for entry in (out_name, physSizeX.value(), physSizeY.value(), physSizeZ.value(),
	                                             stackSizeX, stackSizeY, stackSizeZ)]) + '\n'
            if channelSubfolderPref == "no":
                out_file = os.path.join(outDir, out_name + ".tiff")
                saveImage(imp, out_file)
            elif channelSubfolderPref == "yes":
                out_file = os.path.join(outDir, channel_name, out_name + ".tiff")
                if not os.path.isdir(os.path.join(outDir, channel_name)):
                    os.mkdir(os.path.join(outDir, channel_name))
                saveImage(imp, out_file)
            imageCount += 1

with open(os.path.join(outDir, "VoxelSize.txt"), 'w') as output:
    output.write(voxel_info)

duration = time.time() - startTime
logging.info('Processing finished')

if voxelPref:
	with open(os.path.join(outDir, "VoxelSize.txt"), 'w') as output:
	    output.write(voxel_info)

duration = time.time()- startTime
logging.info('Processing finished')

duration_h, rest = divmod(duration, 3600)
duration_min, rest = divmod(rest, 60)
duration_s = int(round(rest))
if duration_h > 0:
    logging.info('%i files procced in %i h, %i min and %i s', imageCount, duration_h, duration_min, duration_s)
elif duration_min > 0:
    logging.info('%i files procced in %i min and %i s', imageCount, duration_min, duration_s)
else:
    logging.info('%i files procced in %i s', imageCount, duration_s)

IJ.log("\\Clear")
IJ.log("Finished")

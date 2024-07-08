# https://forum.image.sc/t/weka-segmentation-issue-with-python/38180
# Weka result needs LUT

import os
import re
from ij import IJ, WindowManager
from ij.io import FileSaver
from trainableSegmentation import WekaSegmentation
from ij.plugin import LutLoader
from ij.gui import GenericDialog

# Functions to save files
def savetif(img, out_file):
    FileSaver(img).saveAsTiff(out_file + ".tif")

# Function to run the segmentation process
def run_segmentation(inDir, outDir, classDir, lutFile, fileExt, sample_nme_pattern, sample_nme_time_pattern,
                     channel_roi_ec, channel_roi_tm, time_series, composite):

    if not composite and not os.path.isdir(os.path.join(outDir, "composites")):
        os.makedirs(os.path.join(outDir, "composites"))

    if not composite:
        target_files = {sample_nme_time_pattern.match(f).group(1) for f in os.listdir(inDir) if sample_nme_time_pattern.match(f)}
    else:
        target_files = {f for f in os.listdir(inDir) if sample_nme_pattern.match(f)}

    wm = WindowManager

    for f in target_files:
        try:
            if not composite:
                vesselimg_fl = os.path.join(inDir, f + "_C" + channel_roi_ec + ".tif")
                tmimg_fl = os.path.join(inDir, f + "_C" + channel_roi_tm + ".tif")
                vesselimg = IJ.openImage(vesselimg_fl)
                tmimg = IJ.openImage(tmimg_fl)
                IJ.run(vesselimg, "Gaussian Blur...", "sigma=1 scaled")
                IJ.run(vesselimg, "Auto Threshold", "method=Otsu white")
                vesselimg.show()
                tmimg.show()
                IJ.run(vesselimg, "Merge Channels...",
                       "c2=" + vesselimg.getTitle() + " c4=" + tmimg.getTitle() + " create keep")
                vesselimg.changes = False
                tmimg.changes = False
                vesselimg.close()
                tmimg.close()
                merged_image = wm.getImage('Composite')
                savetif(merged_image, os.path.join(outDir, "composites", "composite_" + f))
            else:
                merged_image = IJ.openImage(os.path.join(inDir, f))

            weka = WekaSegmentation()
            weka.setTrainingImage(merged_image)
            weka.loadClassifier(os.path.join(classDir, 'classifier.model'))
            segmented_image = weka.applyClassifier(merged_image, 0, False)
            lut = LutLoader.openLut(lutFile)
            segmented_image.getProcessor().setLut(lut)
            merged_image.close()
            savetif(segmented_image, os.path.join(outDir, "classified_" + f))
        except Exception as e:
            print("Error processing file {}: {}".format(f, e))
            break

# GUI function
def show_gui():
    gd = GenericDialog("Segmentation Parameters")

    # Add fields to the dialog
    gd.addMessage("Select the input and output directories.")
    gd.addDirectoryField("Input Directory:", "/path/to/input", 50)
    gd.addDirectoryField("Output Directory:", "/path/to/output", 50)
    gd.addDirectoryField("Classifier Directory:", "/path/to/classifier", 50)
    gd.addFileField("LUT File:", "/path/to/lut.lut", 50)

    gd.addMessage("What is the file extension of the images?")
    gd.addStringField("File Extension:", ".tif")

    gd.addMessage("Are the images from a time series?")
    gd.addCheckbox("Time Series", True)

    gd.addMessage("Regex patterns for extracting sample name and timepoints from the filename:")
    gd.addStringField("Sample Name Pattern:", "^(\w{3,4})_")
    gd.addStringField("Sample Name Time Pattern:", r'(.+?_T\d{4})_C\d{2}\.tif')

    gd.addMessage("Channels for ROIs:")
    gd.addStringField("Channel ROI EC:", "00")
    gd.addStringField("Channel ROI TM:", "02")

    gd.addMessage("Check if composite images should be created.")
    gd.addCheckbox("Composite", False)

    # Show the dialog
    gd.showDialog()

    if gd.wasCanceled():
        print("Dialog canceled")
        return

    # Get values from the dialog
    inDir = gd.getNextString()
    outDir = gd.getNextString()
    classDir = gd.getNextString()
    lutFile = gd.getNextString()
    fileExt = gd.getNextString()
    time_series = gd.getNextBoolean()
    sample_nme_pattern = re.compile(gd.getNextString())
    sample_nme_time_pattern = re.compile(gd.getNextString())
    channel_roi_ec = gd.getNextString()
    channel_roi_tm = gd.getNextString()
    composite = gd.getNextBoolean()

    # Run the segmentation with the obtained parameters
    run_segmentation(inDir, outDir, classDir, lutFile, fileExt, sample_nme_pattern, sample_nme_time_pattern,
                     channel_roi_ec, channel_roi_tm, time_series, composite)

# Main function to execute GUI and processing
def main():
    show_gui()

# Entry point
if __name__ == "__main__":
    main()

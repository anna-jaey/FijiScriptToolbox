import os
import re
import time
from ij import IJ, WindowManager
from ij.measure import ResultsTable
from ij.gui import Roi
from ij.io import FileSaver
from ij.plugin.frame import RoiManager
from ij.gui import GenericDialog

# Functions to save files
def savetif(img, out_file):
    FileSaver(img).saveAsTiff(out_file + ".tif")

def savepng(img, out_file):
    FileSaver(img).saveAsPng(out_file + ".png")

# Function to run the spheroid analysis to find the right ROIs to make the crop
def run_spheroid_analysis(inDir, outDir, fileExt, sample_nme_pattern, time_pattern, channel_pattern,
                          particle_size_min, scale_factor, channel_roi, resort, time_series):

    if not os.path.isdir(os.path.join(outDir, 'ROI')):
        os.makedirs(os.path.join(outDir, 'ROI'))

    if not os.path.isdir(os.path.join(outDir, 'ROI', "ROIimages")):
        os.makedirs(os.path.join(outDir, 'ROI', "ROIimages"))

    # Initialize Fiji's ROI Manager and ResultsTable
    rm = RoiManager().getInstance()
    rt = ResultsTable.getResultsTable()
    rm.reset()
    rt.reset()
    wm = WindowManager

    sample_name_list = []
    filedct = {}

    # Collect sample names and files based on the regex patterns as provided
    for file in os.listdir(inDir):
        if file.endswith(fileExt) and re.findall(time_pattern, file):
            sample_name = re.findall(sample_nme_pattern, file)[0]
            sample_name_list.append(sample_name)

    sample_name_list = set(sample_name_list)

    # Determine latest time point for each sample if it's a time series
    if time_series:
        for n in sample_name_list:
            timepoint_list = []
            for file in os.listdir(inDir):
                if file.endswith(fileExt) and re.findall(n, file):
                    timepoint = re.findall(time_pattern, file)[0]
                    timepoint_list.append(timepoint)
            filedct.update({n: max(timepoint_list)})

    sample_name_list = set(sample_name_list)
    correct_files = []

    # Filter correct files based on regex criteria
    for key in filedct.keys():
        for file in os.listdir(inDir):
            if time_series:
                if file.endswith(fileExt) and re.findall(channel_pattern, file) and re.findall(key, file):
                    channel = re.findall(channel_pattern, file)[0]
                    timepoint = re.findall(time_pattern, file)[0]
                    if re.match(channel_roi, channel) and timepoint == filedct[key]:
                        correct_files.append(file)
            elif not time_series:
                if file.endswith(fileExt) and re.findall(channel_pattern, file) and re.findall(key, file):
                    channel = re.findall(channel_pattern, file)[0]
                    if re.match(channel_roi, channel):
                        correct_files.append(file)

    # Process each file
    for file in correct_files:
        sample_name = re.findall(sample_nme_pattern, file)[0]
        img = IJ.openImage(os.path.join(inDir, file))
        calibration = img.getCalibration()
        pixel_width = 1 / calibration.pixelWidth
        time.sleep(3)
        IJ.run(img, "Gaussian Blur...", "sigma=1 scaled")
        IJ.run(img, "Auto Threshold", "method=Otsu white")
        IJ.run(img, "Convert to Mask", "")
        IJ.run(img, "Dilate", "")
        IJ.run(img, "Dilate", "")
        IJ.run(img, "Dilate", "")
        IJ.run(img, "Analyze Particles...", "size=" + str(particle_size_min) + "-Infinity show=Overlay summarize overlay add")
        num_rois = rm.getCount()
        roi_list = list(range(0, num_rois, 1))
        for i in roi_list:
            rm.select(img, i)
            rm.runCommand(img, "Measure")
            xpt = rt.getValue("XM", i) * pixel_width
            ypt = rt.getValue("YM", i) * pixel_width
            sidelen = rt.getValue("Major", i) * pixel_width * scale_factor
            roi = Roi(xpt - sidelen / 2, ypt - sidelen / 2, sidelen, sidelen)
            rm.addRoi(roi)
            rm.rename(rm.getCount() - 1, sample_name + "_SpheroidROI_" + str(i))
            rm.select(img, i)
        rm.setSelectedIndexes(roi_list)
        rm.runCommand(img, 'Delete')
        rm.runCommand(img, "Show All")
        rm.runCommand("Set Line Width", "5")
        rm.runCommand("Set Color...", "red")
        imp_flat = img.flatten()
        savepng(imp_flat, os.path.join(outDir, "ROI", 'ROIimages', sample_name))
        rm.runCommand("Save", os.path.join(outDir, "ROI", sample_name + "spheroidROIs.zip"))
        img.close()
        rm.reset()
        rt.reset()

    # Process files for each channel
    for file in os.listdir(inDir):
        if file.endswith(fileExt) and re.findall(channel_pattern, file):
            rm.reset()
            sample_name = re.findall(sample_nme_pattern, file)[0]
            channel = re.findall(channel_pattern, file)[0]
            if time_series:
                timepoint = re.findall(time_pattern, file)[0]

            img = IJ.openImage(os.path.join(inDir, file))
            roipath = os.path.join(outDir, "ROI", sample_name + "spheroidROIs.zip")
            rm.open(roipath)
            num_rois = rm.getCount()
            roi_list = list(range(0, num_rois, 1))
            for i in roi_list:
                cropped = img.duplicate()
                rm.select(cropped, i)
                cropped = cropped.crop()
                roiname = rm.getName(i)
                if time_series:
                    outname = roiname + "_T" + timepoint + "_C" + channel
                else:
                    outname = roiname + "_C" + channel
                savetif(cropped, os.path.join(outDir, outname))
            img.close()

    # Save no of spheroids
    win = wm.getWindow("Summary")
    summary_rt = win.getTextPanel().getResultsTable()
    summary_rt.save(os.path.join(outDir, "spheroid_count.csv"))

    # Resort
    files = [f for f in os.listdir(outDir) if os.path.isfile(os.path.join(outDir, f)) and f.endswith(".tif")]
    for f in files:
        if resort == "Sample":
            sample_name = re.findall(sample_nme_pattern, f)[0]
            resort_folder = os.path.join(outDir, sample_name)
            if not os.path.exists(resort_folder):
                os.makedirs(resort_folder)
            os.rename(os.path.join(outDir, f), os.path.join(resort_folder, f))
        elif resort == "Timepoint":
            timepoint = re.findall(time_pattern, file)[0]
            resort_folder = os.path.join(outDir, timepoint)
            if not os.path.exists(resort_folder):
                os.makedirs(resort_folder)
            os.rename(os.path.join(outDir, f), os.path.join(resort_folder, f))
        elif resort == "Channel":
            channel = re.findall(channel_pattern, file)[0]
            resort_folder = os.path.join(outDir, channel)
            if not os.path.exists(resort_folder):
                os.makedirs(resort_folder)
            os.rename(os.path.join(outDir, f), os.path.join(resort_folder, f))

# GUI
def show_gui():
    gd = GenericDialog("Spheroid Analysis Parameters")

    # Add fields to the dialog
    gd.addMessage("Select the input and output directories.")
    gd.addDirectoryField("Input Directory:", "/path/to/input", 50)
    gd.addDirectoryField("Output Directory:", "/path/to/output", 50)

    gd.addMessage("What is the file extension of the images?")
    gd.addStringField("File Extension:", ".tif")

    gd.addMessage("Regex patterns for extract sample name, timepoints, and channels from the filename:")
    gd.addStringField("Sample Name Pattern:", "^(\w{3,4})_")
    gd.addStringField("Time Pattern:", r'-t(\d{4})')
    gd.addStringField("Channel Pattern:", r'-C(\d{2})')

    gd.addMessage("Minimum size for analyze particles to find a spheroid.")
    gd.addNumericField("Min Particle Size:", 2000, 0)
    gd.addMessage("Factor by which the major axis is being scaled.")
    gd.addNumericField("Scale Factor:", 1.5, 1)

    gd.addMessage("Which channel contains the spheroids?")
    gd.addStringField("Channel ROI:", "01")

    gd.addMessage("Check if the experiments is a time series.")
    gd.addCheckbox("Time Series", True)

    gd.addMessage("Do you want the cropped images to be sorted?")
    gd.addChoice("Resort Output:", ["None", "Sample", "Timepoint (if time series)", "Channel"],
                 "None")

    # Show the dialog
    gd.showDialog()

    if gd.wasCanceled():
        print("Dialog canceled")
        return

    # Get values from the dialog
    inDir = gd.getNextString()
    outDir = gd.getNextString()
    fileExt = gd.getNextString()
    sample_nme_pattern = gd.getNextString()
    time_pattern = gd.getNextString()
    channel_pattern = gd.getNextString()
    particle_size_min = int(gd.getNextNumber())
    scale_factor = gd.getNextNumber()
    channel_roi = gd.getNextString()
    time_series = gd.getNextBoolean()
    resort = gd.getNextChoice()

    # Run the spheroid analysis with the obtained parameters
    run_spheroid_analysis(inDir, outDir, fileExt, sample_nme_pattern, time_pattern, channel_pattern,
                          particle_size_min, scale_factor, channel_roi, resort, time_series)

# Main function to execute GUI and processing
def main():
    show_gui()

# Entry point
if __name__ == "__main__":
    main()

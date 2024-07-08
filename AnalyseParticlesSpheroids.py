import os
import re
import csv
from ij import IJ, WindowManager
from ij.io import FileSaver
from ij.plugin.frame import RoiManager
from ij.gui import GenericDialog, Roi
from ij.plugin import Duplicator
from ij.plugin.filter import ParticleAnalyzer
from ij.measure import ResultsTable

# Function to save images as TIFF
def savetif(img, out_file):
    FileSaver(img).saveAsTiff(out_file + ".tif")

# Function to save images as PNG
def savepng(img, out_file):
    FileSaver(img).saveAsPng(out_file + ".png")

# Function to set up directories
def setup_directories(outDir):
    if not os.path.isdir(outDir):
        os.makedirs(outDir)
    for subdir in ['ROI', 'SphereMeasurements', 'overlay']:
        if not os.path.isdir(os.path.join(outDir, subdir)):
            os.makedirs(os.path.join(outDir, subdir))

# Function to process images and analyze particles
def process_images(inDir_segmented, indir_cropped, outDir, fileExt, sample_nme_pattern, sample_nme_time_pattern, segmented_nme_pattern, re_crop, time_series, scale_factor, channel_spheroid, particle_size_min):
    dupl = Duplicator()
    rtt = ResultsTable().getResultsTable()
    rt = ResultsTable().getResultsTable()
    wm = WindowManager

    IJ.run("Set Measurements...", "area mean center fit redirect=None decimal=0")

    # find the WEKA classified files and the matching tifs in the same folder
    fl_dict = dict()
    if time_series:
        for file in os.listdir(inDir_segmented):
            if file.endswith(fileExt) and re.findall(segmented_nme_pattern, file) and re.findall(
                    sample_nme_time_pattern, file):
                segment_file = os.path.join(inDir_segmented, file)
                sample = re.findall(sample_nme_time_pattern, file)[0]
                for targetfile in os.listdir(indir_cropped):
                    if (targetfile.endswith(fileExt) and re.findall(sample, targetfile)) and re.findall(
                            channel_spheroid, targetfile):
                        fl = os.path.join(indir_cropped, targetfile)
                fl_dict.update({fl: segment_file})

    else:
        for file in os.listdir(inDir_segmented):
            if file.endswith(fileExt) and re.findall(segmented_nme_pattern, file) and re.findall(sample_nme_pattern,
                                                                                                 file):
                segment_file = os.path.join(inDir_segmented, file)
                sample = re.findall(sample_nme_pattern, file)[0]
                for targetfile in os.listdir(indir_cropped):
                    if (targetfile.endswith(fileExt) and re.findall(sample, targetfile)):
                        fl = os.path.join(indir_cropped, targetfile)
                fl_dict.update({fl: segment_file})

    for key in fl_dict:
        rt = ResultsTable().getResultsTable()
        rm = RoiManager().getInstance()
        rm.reset()
        img = IJ.openImage(fl_dict[key])
        img = dupl.run(img, 1, 1, 1, 1, 1, 1)
        targetimg = IJ.openImage(key)
        if time_series:
            sample = re.findall(sample_nme_time_pattern, key)[0]
        else:
            sample = re.findall(sample_nme_pattern, key)[0]

        targetimg = dupl.run(targetimg, 1, 1, 1, 1, 1, 1)
        IJ.run(targetimg, "Gaussian Blur...", "sigma=1 scaled")
        IJ.run(targetimg, "Auto Threshold", "method=Otsu white")
        IJ.run(targetimg, "Convert to Mask", "")
        IJ.run(targetimg, "Dilate", "")
        IJ.run(targetimg, "Dilate", "")
        IJ.run(targetimg, "Erode", "")
        IJ.run(targetimg, "Erode", "")
        IJ.run(targetimg, "Dilate", "")
        IJ.run(targetimg, "Analyze Particles...",
               "size=" + str(particle_size_min) + "-Infinity show=Overlay display exclude clear add")

        # re-crop around the spheroid if needed
        if re_crop:
            if rm.getCount() > 1:
                IJ.log("Skipping" + key + "because more than 1 tROI")
                targetimg = targetimg
                continue
            else:
                calibration = targetimg.getCalibration()
                resol = 1 / calibration.pixelWidth
                xpt = rt.getValue("XM", 0) * resol
                ypt = rt.getValue("YM", 0) * resol
                sidelen = rt.getValue("Major", 0) * resol * scale_factor
                roi = Roi(xpt - sidelen / 2, ypt - sidelen / 2, sidelen, sidelen)
                rm.addRoi(roi)
                rm.select(targetimg, 1)
                targetimg = targetimg.crop()
                rm.select(img, 1)
                img = img.crop()
        IJ.run(targetimg, "Select None", "")
        # get the spheroid to measure to size
        IJ.run(targetimg, "Analyze Particles...",
               "size=" + str(particle_size_min) + "-Infinity show=Overlay display exclude clear summarize add")
        rt.save(os.path.join(outDir, 'SphereMeasurements', sample + "measurements.csv"))
        IJ.run(targetimg, "Select None", "")
        IJ.run(img, "Select None", "")
        rm.reset()

        # get vessel ROI
        IJ.run(img, "Auto Threshold", "method=Default white")
        IJ.run(img, "Convert to Mask", "")
        IJ.run(img, "Invert", "")
        IJ.run(img, "Dilate", "")
        IJ.run(img, "Erode", "")
        IJ.run(img, "Erode", "")
        IJ.run(img, "Erode", "")
        IJ.run(img, "Dilate", "")
        IJ.run(img, "Dilate", "")
        IJ.run(img, "Dilate", "")
        IJ.run(img, "Erode", "")
        IJ.run(img, "Dilate", "")
        IJ.run(img, "Erode", "")
        IJ.run(img, "Dilate", "")
        IJ.run(img, "Analyze Particles...", "size=100-Infinity circularity=0.0-1.00 summarize add composite")
        win = wm.getWindow("Summary")
        rtt = win.getTextPanel().getResultsTable()
        num_rois = rm.getCount()
        roi_list = list(range(0, num_rois, 1))
        rm.setSelectedIndexes(roi_list)
        if num_rois > 1:
            rm.runCommand(img, "Combine")
            rm.runCommand(img, 'Add')
            rm.setSelectedIndexes(roi_list)
            rm.runCommand(img, 'Delete')
        else:
            rm.setSelectedIndexes(roi_list)
        rm.runCommand("Save", os.path.join(outDir, "ROI", sample + "vROIs.zip"))  # save the vROIs

        # vROI on the spheroid image

        rm.select(targetimg, 0)
        IJ.run(targetimg, "Make Inverse", "")
        IJ.run(targetimg, "Clear", "slice")
        rm.reset()
        rt.reset()
        IJ.run(targetimg, "Select None", "")
        IJ.run(img, "Select None", "")

        IJ.run(targetimg, "Analyze Particles...", "size=50-Infinity circularity=0.50-1.00 exclude summarize add")
        if rm.getCount() > 0:
            rm.runCommand("Save", os.path.join(outDir, "ROI", sample + "tROIs.zip"))  # save the tROI
        IJ.run(img, "Green", "")
        targetimg.show()
        img.show()
        IJ.run(targetimg, "Add Image...", "image=[" + img.getTitle() + "] x=0 y=0 opacity=40")
        savepng(targetimg, os.path.join(outDir, "overlay", sample))
        targetimg.changes = False
        targetimg.close()
        img.changes = False
        img.close()
    rtt.save(os.path.join(outDir, "arearatio.csv"))
    rtt.reset()


def clean_area_ratio_csv(outDir, sample_nme_pattern, sample_nme_time_pattern, time_series):
    i = 0
    with open(os.path.join(outDir, "arearatio.csv"), mode='r') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        if fieldnames is None:
            print("Error: The input file is empty or the header row is missing.")
            return

        with open(os.path.join(outDir, "arearatio_cleaned.csv"), mode='wb') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                i += 1
                if time_series:
                    sample = re.findall(sample_nme_time_pattern, row['Slice'])[0]
                else:
                    sample = re.findall(sample_nme_pattern, row['Slice'])[0]
                if i == 1:
                    row['Slice'] = sample + "_spheroid"
                elif i == 2:
                    row['Slice'] = sample + "_vessel"
                elif i == 3:
                    row['Slice'] = sample + "_overlayparticles"
                    i = 0
                writer.writerow(row)

# GUI
def show_gui():
    gd = GenericDialog("Segmentation and Analysis Parameters")

    gd.addMessage("Select the input and output directories.")
    gd.addDirectoryField("Segmented Input Directory:", "/path/to/segmented", 50)
    gd.addDirectoryField("Cropped Input Directory:", "/path/to/cropped", 50)
    gd.addDirectoryField("Output Directory:", "/path/to/output", 50)

    gd.addMessage("What is the file extension of the images?")
    gd.addStringField("File Extension:", ".tif")

    gd.addMessage("Regex patterns for extracting sample name and timepoints from the filename:")
    gd.addStringField("Sample Name Pattern:", r'_?(\w{3,4}_SpheroidROI_\d{1,2})_')
    gd.addStringField("Sample Name Time Pattern:", r'_?(\w{3,4}_SpheroidROI_\d{1,2}_T\d{3,4})')
    gd.addStringField("Segmented Name Pattern:", r'classified_')

    gd.addMessage("Are the images from a time series?")
    gd.addCheckbox("Time Series", True)

    gd.addMessage("Re-crop around the spheroids?")
    gd.addCheckbox("Re-crop", True)
    gd.addNumericField("Scale Factor", 1.15, 1)

    gd.addMessage("Which channel contains the spheroids?")
    gd.addStringField("Channel Spheroid:", "_C01")

    gd.addMessage("Minimum size for analyze particles to find a spheroid.")
    gd.addNumericField("Particle Size Minimum:", 2000, 0)

    gd.showDialog()
    if gd.wasCanceled():
        return

    # Get values from the dialog
    inDir_segmented = gd.getNextString()
    indir_cropped = gd.getNextString()
    outDir = gd.getNextString()
    fileExt = gd.getNextString()
    sample_nme_pattern = gd.getNextString()
    sample_nme_time_pattern = gd.getNextString()
    segmented_nme_pattern = gd.getNextString()
    time_series = gd.getNextBoolean()
    re_crop = gd.getNextBoolean()
    scale_factor = gd.getNextNumber()
    channel_spheroid = gd.getNextString()
    particle_size_min = gd.getNextNumber()

    setup_directories(outDir)
    process_images(inDir_segmented, indir_cropped, outDir, fileExt, sample_nme_pattern, sample_nme_time_pattern,
                   segmented_nme_pattern, re_crop, time_series, scale_factor, channel_spheroid, particle_size_min)
    #clean_area_ratio_csv(outDir, sample_nme_pattern, sample_nme_time_pattern, time_series)


def main():
    show_gui()

if __name__ == "__main__":
    main()

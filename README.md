# ImageJ/Fiji Script Toolbox

This is a collection of `Python`/`Jython` scripts to automate image processing.

## Particle counting and area ratio quantification in multi-channel fluorescence images

This set of scripts analyses marker-positive particles within segmented vessel areas in proximity to marker-positive spheroids.

### Workflow Overview

1. **`cropROI.py`**: Crops individual spheroids (ROI) from images containing multiple spheroids for further analysis.
   - Determines cropping ROI by analysing particles above a specified size threshold to identify spheroids.
   - Draws an ROI as a square scaled by a factor of the major axis of an ellipse fitted around the spheroid.
   - Outputs include cropped images, ROI coordinates, and an image marking the detected spheroids.

   ![cropROI.py](docs/screenshots/cropROI.png?raw=True)

   Select paths for IO as well as the file extension of the image files to be processed.
   Check the box if the image series is a time series.
   Add the regex patterns for the script to recognize the sample name, timepoint, and channel.
   Select the minimum size of a spheroid (µm² or pixel² depending on image metadata).
   The script fits an ellipse around the spheroid. Scale factor is the factor by which the major axis is scaled to create the ROI.
   Indicate which channel contains the spheroid.
   Output sorting: the script can sort the cropped images according to sample, timepoint, channel, or not at all.

2. **`SegmentVesselsWeka.py`**: Segments vessels using a trained Weka model, optimised for composite images of marker-expressing vessels (endothelial cells (EC)) and transmitted light (TM).
   - Reads cropped files and creates composites of relevant channels.
   - Outputs segmented vessel images for use in `AnalyseParticlesSpheroids.py`.

   ![SegmentVesselsWeka.py](docs/screenshots/SegmentVesselsWeka.png?raw=True)

   Select paths for IO as well as the file extension of the image files to be processed.
   Select path for LUT, can be found under ./res/ClassifiedImageLUT.lut See also: [https://forum.image.sc/t/weka-segmentation-issue-with-python/38180](https://forum.image.sc/t/weka-segmentation-issue-with-python/38180).
   Check the box if the image series is a time series.
   Add the regex patterns for the script to recognise the sample name, timepoint, and channel.
   Add which channels are relevant for the vessel segmentation.
   If using images that are composites already, check 'Composite'.

3. **`AnalyseParticlesSpheroids.py`**: Analyzes particles within the segmented vessel area, in proximity of spheroids.
   - Recrops to areas near spheroids if necessary and measures spheroid size.
   - Overlays vessel ROI from Weka-classified images onto spheroid channels to count particles and measure vessel area.
   - Outputs CSV with measurements of spheroids, vessels, and overlay particles.

   ![AnalyseParticlesSpheroids.py](docs/screenshots/AnalyseParticlesSpheroid.png?raw=True)

   Select paths for IO as well as the file extension of the image files to be processed.
   Add the regex patterns for the script to recognize the sample name, timepoint, and the name of the Weka-segmented image (from `SegmentVesselsWeka.py`).
   Check the box if the image series is a time series and if recropping around the spheroid is required.
   Select the minimum size of a spheroid (µm² or pixel² depending on image metadata).
   As before, the scripts fit an ellipse around the spheroid. The scale factor is the factor by which the major axis is scaled to create the ROI.
   Indicate which channel contains the spheroid.

### Notes

- Optimized for TIFF files with single images per channel and timepoint, adaptable to other formats.
- Each script can be used independently with different inputs.
- Adjustments needed for different inputs.

## `ZProject.py`

This script uses the [Bioformats](https://www.openmicroscopy.org/bio-formats/) plugin to read proprietary microscopy image formats into ImageJ.
If the input image contains several channels, they will be split into several files and the channel name will be added to the filename.
A z-projection will be obtained and saved.
Additionally, a txt file with the voxel sizes for each output image is created.

![](docs/screenshots/ZProject.png?raw=True)

First, set the extension of the image files from the microscopy software, e.g. `nd2`.
The output can be in a new folder without subfolders (*recommended*) or the input directory tree can be recreated in the output folder.
Be aware, that if the filenames between subfolders are equal, the images will get overwritten or not processed, depending on the next option. **Best practice is to use unique filenames.**
Alternatively, the output files can be written within the subfolders of the input directory.  
The channels of the input image are split into single files which can be separated in subfolders (*recommended*).  
Choose the methods for the z-projection.
Tick the box if the images need to be converted to RGB (e.g. for processing in Angiotool).
Select the file format to save the z-projections (both `.tiff` and `.jpg` can be selected).
Tick the last option if you would like to save `.tiff` files of the z-stack images.

## `split_channels.py`

This script uses the [Bioformats](https://www.openmicroscopy.org/bio-formats/) plugin to read proprietary microscopy image formats into ImageJ.  
Set the file extension (e.g. `.nd2`) in the first dialogue box.
Also, indicated whether the images of the different channels should be saved in subfolders.
The file name of the saved image will contain the channel name either way.
Untick the voxel size box, if a `.txt` file with the voxel sizes isn't needed.
If maximum intensity projections are needed, use `ZProject.py`.

## `histo_splitter.py`

This script reads in an image of a complete histology slide, lets the user set ROIs and saves the cropped ROIs.

![Options](docs/screenshots/HistoSplitterOptions.png?raw=True){width="50%"}

First, set the file extension of the input images and provide a string to identify the input images.
If the string is empty, all images of that input folder matching the file extension are processed.
The output images can be saved in a new directory without subfolders (images with equal filenames will be overwritten).
A new output directory can be created with the input directory tree.
Or the output can be saved within the input folder.
The following dialogs will prompt to select an input and output folder.  
If the script was stopped previously, it can continue from the stopping point by selecting 'yes'.
The txt files with the progress information needs to be provided (see also below).


![Use](docs/screenshots/HistoSplitterUse.png?raw=True)

The image will open with the first ROI drawn.
Re-draw or change the ROI and draw further ROIs as desired.
Make sure to add them to the ROI manager (press *t* or click on Add).
Upon clicking on "ok" in the Action required window, the script crops the image at the ROIs and saves the cropped images.  
A zip folder with the ROI information will be saved in the same folder as the input image.
This can be imported into Fiji again.  
A PhysicalSize.txt file is saved in the output directory which contains the pixel size in x and y (in µm/px) as well as the width and height of the image (in pixel).  
The script can be stopped at any image by NOT adding any ROI and click 'okay' twice.
A file (ProcessedFiles.txt) is saved with the progress.
To continue, this file needs to be provided to the script in the next run.  
Moreover, a Log.txt file is saved in the output folder.

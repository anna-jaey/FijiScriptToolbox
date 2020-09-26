# ImageJ/Fiji Script Toolbox

This is a collection of `Python`/`Jython` scripts to automate image processing.

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

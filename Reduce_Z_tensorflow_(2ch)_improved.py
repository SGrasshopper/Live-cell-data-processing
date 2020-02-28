from net.imglib2.img.display.imagej import ImageJFunctions
from java.awt.event import TextListener
from ij import Menus
from ij.gui import GenericDialog
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog
from ij.plugin import ZProjector
from ij.plugin import ChannelSplitter
from ij.plugin import RGBStackMerge
from ij.plugin import HyperStackConverter
import java.util.ArrayList as ArrayList
from ij import ImagePlus
import csv
import os
import sys
from ij import IJ

def reduceZ():
    imp = IJ.getImage()  #get the standardtack
    title_1 = imp.getTitle()
    title = title_1.split(' - ')[1]
    print(title)
    dimentions = imp.getDimensions()
    numZ, numChannels, numframes  = dimentions[3], dimentions[2], dimentions[4]
    print(numChannels)
   
    IJ.run(imp,"Set Measurements...", "mean redirect=None decimal=4")
    #IJ.run(imp, "Set Measurements...", "skewness redirect=None decimal=2")
    
    kurtTotal = []
    for time in range(numframes):
        print(time)
        time = time+1
        imp.setPosition(1, 1, time)
        kurt = []
        for z in range(numZ):
            z = z+1
            imp.setPosition(1, z, time)
            imp.setRoi(102, 69, 354, 373)
            #duplicate image here to get an image to run 
            imp.copy()
            imp_2 = imp.getClipboard()
            imp_2.show()
            IJ.run(imp_2, "Microscope Image Focus Quality", "originalimage=Clipboard tilecountx=5 tilecounty=5 createprobabilityimage=true overlaypatches=false solidpatches=false borderwidth=4")
            IJ.selectWindow('Probabilities')
            imp_1 = IJ.getImage()
            IJ.run(imp_1, "Measure", "")
            rt = ResultsTable()
            t = rt.getResultsTable()
            kurt.append(t.getValueAsDouble(1, z-1)) # 1 = mean 
            imp_1.close()
            imp_2.close()   
        kurtTotal.append(kurt.index(max(kurt))+1)
        IJ.run(imp, "Clear Results", "")
    print(kurtTotal)
    
    IJ.run(imp, "Select All", "")

    imp2 = IJ.createImage("GFP", "16-bit black", dimentions[0], dimentions[1], numframes)
    imp2 = HyperStackConverter.toHyperStack(imp2, 1, 1, numframes, "Color")
    #imp2.show()
    print(' ------------')
    print(numframes)
    channel = 1
    i = 0
    for time in range(numframes):
        time = time+1
        imp.setPosition(channel, kurtTotal[i], time)
        imp.copy()
        imp2.setPosition(channel, 1, time)
        imp2.paste()
        print(time)
        #IJ.run(imp2, "Add Slice", "")
        i=i+1
    IJ.run(imp2, "Delete Slice", "delete=slice")
    imp2.show()
    
    imp4 = IJ.createImage("RFP", "16-bit black", dimentions[0], dimentions[1], numframes)
    imp4 = HyperStackConverter.toHyperStack(imp4, 1, 1, numframes, "Color")
    #imp4.show()
    print(' ------------')
    channel = 2  
    i = 0
    for time in range(numframes):
        time = time+1
        imp.setPosition(channel, kurtTotal[i], time)
        imp.copy()
        print(imp.title)
        imp4.setPosition(channel, 1, time)
        imp4.paste()
        #IJ.run(imp4, "Add Slice", "")
        i=i+1
    IJ.run(imp4, "Delete Slice", "delete=slice")
    imp4.show()

    IJ.selectWindow(title_1)
    IJ.run("Close")
    
    imp5 = ImagePlus()
    IJ.run(imp5, "Merge Channels...", "c1=RFP c2=GFP create")
    imp5 = IJ.getImage()
    #imp5 = HyperStackConverter.toHyperStack(imp5, 2, 1, numframes, "Color")
    #imp5.setDimensions(numChannels, 1, numframes)
    IJ.run(imp5, "Bio-Formats Exporter", "save=/home/rickettsia/Desktop/data/Clamydial_Image_Analysis/EMS_BMEC_20X_12042019/Zreduced/" + title + ".ome.tif export compression=LZW")
    IJ.selectWindow('Merged')
    IJ.run("Close")

od = OpenDialog("Time Laps Images", "")
firstDir = od.getDirectory()
fileList = os.listdir(firstDir)

if "DisplaySettings.json" in fileList:
    fileList.remove("DisplaySettings.json")
if ".DS_Store" in fileList:  
    fileList.remove(".DS_Store")  
#print(firstDir + fileList[0])
fileList.sort()
i = 1
for fileName in fileList:
    IJ.run("Collect Garbage")
    currentFile = firstDir + fileName
    print(firstDir)
    IJ.run("Bio-Formats Importer", "open=[" + currentFile + "] color_mode=Default split_channels view=Hyperstack stack_order=XYCZT series_list="+str(i))
    #IJ.run("Bio-Formats Importer", "open=[" + currentFile + "] color_mode=Composite view=Hyperstack stack_order=XYCZT use_virtual_stack")
    #IJ.run("Bio-Formats Importer", "open=[" + currentFile + "] color_mode=Composite view=Hyperstack stack_order=XYCZT")
    #IJ.run("Bio-Formats Windowless Importer", "open=" + currentFile)
    #imp = IJ.openImage(currentFile)
    #imp.show()
    reduceZ()
    i=i+1
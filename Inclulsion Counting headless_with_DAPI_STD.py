import os
import sys
import time
from decimal import Decimal
from java.awt import Color
from java.awt.event import TextListener
from ij import IJ
from ij import Menus
from ij.gui import GenericDialog
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog
from ij.plugin import ChannelSplitter
from ij.plugin import ImageCalculator
from net.imglib2.img.display.imagej import ImageJFunctions
from java.awt.event import TextListener
from ij.measure import ResultsTable
import java.util.ArrayList as ArrayList
import csv
from ij import ImagePlus

od = OpenDialog("Titer_files", "")
firstDir = od.getDirectory()
fileList = os.listdir(firstDir)

if "DisplaySettings.json" in fileList:
    fileList.remove("DisplaySettings.json")
if ".DS_Store" in fileList:  
    fileList.remove(".DS_Store")  
global fileName

myfile = open('/home/rickettsia/Desktop/data/Titering/Fancy_Tet_titer/data_2_csv/HctB_48H_with_atc_2.csv', 'wb')
wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
wr.writerow(["well", "position", "inclusion_num", "DAPI", "DAPI_STD"])

IJ.run("Set Measurements...", "area mean standard min kurtosis redirect=None decimal=3")

totalCount = []
i = 1
fileList.sort()
for fileName in fileList:
    #IJ.run("Collect Garbage")
    #ip = IJ.getImage()
    currentFile = firstDir + fileName
    print("")
    print(currentFile)
    ip = IJ.openImage(currentFile)
    #ip.show()
    fileName = ip.title
    IJ.run(ip, "Set Scale...", "distance=0")
    IJ.run(ip, "Gaussian Blur...", "sigma=3")
    IJ.run(ip, "Unsharp Mask...", "radius=4 mask=0.60")
    IJ.run(ip, "Subtract Background...", "rolling=50")
    IJ.run(ip, "Enhance Contrast...", "saturated=0.3")
    #imp.setRoi(318, 246, 1581, 1647)
    IJ.setAutoThreshold(ip, "MaxEntropy dark")
    IJ.run(ip, "Measure", "")
    IJ.resetThreshold(ip)
    rt = ResultsTable()
    rt = rt.getResultsTable()
    DAPI_sig = rt.getValueAsDouble(1, 0)
    D_kurt = rt.getValueAsDouble(2, 0) #standard deviation
    IJ.run("Clear Results")
    
    channels = ChannelSplitter.split(ip)
    imp_DAPI = channels[0]
    imp_GFP = channels[1]
    #IJ.selectWindow(fileName)
    #IJ.run("Close")
    #imp_GFP.show()
    
    IJ.setThreshold(imp_GFP, 1111, 65536)
    IJ.run(imp_GFP, "Make Binary", "")
    IJ.run(imp_GFP, "Fill Holes", "")
    IJ.run(imp_GFP, "Watershed", "")
    IJ.run("Clear Results")

    IJ.run(imp_GFP, "Analyze Particles...", "size=200-2000 circularity=0.25-1.00 show=Nothing display include")
    print(fileName)                                                                                                                                                    
    rt = ResultsTable()
    rt = rt.getResultsTable()
    numInclusions = rt.getCounter()
    print('inclusions counted')
    print(numInclusions)                                                                                                                                                                    
    well = fileName.split('_')[5]
    well = well.split('-')[0]
    position = fileName.split('_')[6]
    position = position.split('.')[0]
    print(well)
    print(position)
    l1 = (well, position, numInclusions, DAPI_sig,  D_kurt)
    wr.writerow(l1)
    print(l1)
    #wr.writerow('')
    IJ.run("Clear Results")
    i = i+1
    print(i)
    #IJ.selectWindow('C2-'+fileName)
    #IJ.run("Close")

myfile.close()

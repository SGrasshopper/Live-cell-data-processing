from fiji.plugin.trackmate.detection import BlockLogDetectorFactory
from fiji.plugin.trackmate.detection import LogDetectorFactory
from fiji.plugin.trackmate.features.spot import SpotIntensityAnalyzerFactory
from fiji.plugin.trackmate.features.spot import SpotContrastAndSNRAnalyzerFactory
import fiji.plugin.trackmate.tracking.sparselap.SparseLAPTrackerFactory as SparseLAPTrackerFactory
import fiji.plugin.trackmate.extra.spotanalyzer.SpotMultiChannelIntensityAnalyzerFactory as SpotMultiChannelIntensityAnalyzerFactory
from fiji.plugin.trackmate.tracking.sparselap import SparseLAPTrackerFactory
from fiji.plugin.trackmate.tracking.oldlap import SimpleLAPTrackerFactory
from fiji.plugin.trackmate.tracking import LAPUtils
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import fiji.plugin.trackmate.features.track.TrackDurationAnalyzer as TrackDurationAnalyzer
import fiji.plugin.trackmate.features.track.TrackSpotQualityFeatureAnalyzer as TrackSpotQualityFeatureAnalyzer
import fiji.plugin.trackmate.SelectionModel as SelectionModel
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.Settings as Settings
import fiji.plugin.trackmate.Model as Model
import fiji.plugin.trackmate.TrackMate as TrackMate
import fiji.plugin.trackmate.Spot as Spot

from net.imglib2.img.display.imagej import ImageJFunctions
from java.awt.event import TextListener
from ij import Menus
from ij.gui import GenericDialog
from ij.io import OpenDialog
from ij.measure import ResultsTable
from ij.gui import WaitForUserDialog
import java.util.ArrayList as ArrayList
import csv
import os
import sys
from ij import IJ

def track():
    imp = IJ.getImage()  #Use this to get name that bioformats assigns that is unpredicatble
    orgtitle = imp.getTitle()
    IJ.run("Z Project...", "projection=[Sum Slices] all")
    #IJ.run("Grouped Z Project...", "projection=[Sum Slices] group=4")
    IJ.selectWindow(orgtitle)
    IJ.run("Close")
    imp = IJ.getImage()  #Use this to get name that bioformats assigns that is unpredicatble
    title = imp.getTitle()
    print(title)
    #IJ.run("Split Channels")
    #DICImage = 'C1-' + title
    #IJ.run("Deinterleave", "how=3")
    #DicImage =  title + ' #1'
    #IhtAImage = title + ' #2'
    #HctAImage = title + ' #3'
    #IJ.selectWindow(DicImage)
    #IJ.run('Close')
    #IJ.run("Merge Channels...", "c2=[" + IhtAImage + ']'+ " c1=[" + HctAImage + ']'+" create")
    IJ.run("Subtract Background...", "rolling=50 sliding stack")
    IJ.run("Enhance Contrast...", "saturated=0.3")
    #IJ.run("Gaussian Blur...", "sigma=1 stack")
    #IJ.run("Unsharp Mask...", "radius=1 mask=0.60 stack")
    IJ.run("Multiply...", "value=10 stack")
    IJ.run("Subtract Background...", "rolling=50 sliding stack")
    IJ.run("Set Scale...", "distance=0")
    
    imp = IJ.getImage()
    title = imp.getTitle()
    IJ.run(imp, "Set Scale...", "distance=0")

    # Get the number of channels 
    nChannels = imp.getNChannels()
    
    # Setup settings for TrackMate
    settings = Settings()
    settings.setFrom(imp)
    #settings.dt = 0.05
    
    # Spot analyzer: we want the multi-C intensity analyzer.
    settings.addSpotAnalyzerFactory(SpotMultiChannelIntensityAnalyzerFactory())
    #settings.addSpotAnalyzerFactory(SpotIntensityAnalyzerFactory())
    #settings.addSpotAnalyzerFactory(SpotContrastAndSNRAnalyzerFactory())   

    
    # Spot detector.
    settings.detectorFactory = LogDetectorFactory()
    settings.detectorSettings = settings.detectorFactory.getDefaultSettings()
    settings.detectorSettings['RADIUS'] = 23.0
    settings.detectorSettings['THRESHOLD'] = 0.0
    
    # Spot tracker.
    # Configure tracker - We don't want to allow merges or splits
    settings.trackerFactory = SparseLAPTrackerFactory()
    #settings.trackerFactory = SimpleLAPTrackerFactory() 
    settings.trackerSettings = LAPUtils.getDefaultLAPSettingsMap() # almost good enough
    settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = False
    settings.trackerSettings['ALLOW_TRACK_MERGING'] = False
    settings.trackerSettings['LINKING_MAX_DISTANCE'] = 15.0
    settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = 15.0
    settings.trackerSettings['MAX_FRAME_GAP'] = 1
    
     # Configure track filters
    settings.addTrackAnalyzer(TrackDurationAnalyzer())
    settings.addTrackAnalyzer(TrackSpotQualityFeatureAnalyzer())
    #TRACK_MEAN_QUALITY 
    #TRACK_MAX_QUALITY
    #TRACK_MIN_QUALITY
    #TRACK_MEDIAN_QUALITY
    #TRACK_STD_QUALITY    
    #TRACK_DURATION
    #TRACK_START 
    #TRACK_STOP 
    #TRACK_DISPLACEMENT 
    #NUMBER_SPOTS
    #NUMBER_GAPS 
    #LONGEST_GAP 
    #NUMBER_SPLITS 
    #NUMBER_MERGES 
    #NUMBER_COMPLEX 
    
    filter1 = FeatureFilter('TRACK_DURATION', 15, True)
    settings.addTrackFilter(filter1)
    #filter2 = FeatureFilter('TRACK_START', 25000, False)
    #settings.addTrackFilter(filter2)
    #filter3 = FeatureFilter('TRACK_STOP', 25, True)
    #settings.addTrackFilter(filter3)
    #filter4 = FeatureFilter('TRACK_STD_QUALITY', 0.08, True)
    #settings.addTrackFilter(filter4)
    
    # Run TrackMate and store data into Model.
    model = Model()
    trackmate = TrackMate(model, settings)
    
    ok = trackmate.checkInput()
    if not ok:
        sys.exit(str(trackmate.getErrorMessage()))
            
    ok = trackmate.process()
    if not ok:
        sys.exit(str(trackmate.getErrorMessage()))
    
    selectionModel = SelectionModel(model)
    displayer =  HyperStackDisplayer(model, selectionModel, imp)
    displayer.render()
    displayer.refresh()
    
    IJ.log('TrackMate completed successfully.')
    IJ.log('Found %d spots in %d tracks.' % (model.getSpots().getNSpots(True) , model.getTrackModel().nTracks(True)))
    
    # Print results in the console.
    headerStr = '%10s %10s %10s %10s %10s %10s' % ('Spot_ID', 'Track_ID', 'Frame', 'X', 'Y', 'Z')
    rowStr = '%10d %10d %10d %10.1f %10.1f %10.1f'
    for i in range( nChannels ):
        headerStr += (' %10s' % ( 'C' + str(i+1) ) )
        rowStr += ( ' %10.1f' )
    
    #open a file to save results
    myfile = open('/home/rickettsia/Desktop/data/Clamydial_Image_Analysis/gamma_interferon_101518/'+orgtitle.split('.')[0]+'.csv', 'wb')
    wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
    wr.writerow(['Spot_ID', 'Track_ID', 'Frame', 'X', 'Y', 'Z', 'Channel_1', 'Channel_2'])
    
    IJ.log('\n')
    IJ.log(headerStr)
    tm = model.getTrackModel()
    trackIDs = tm.trackIDs(True)
    for trackID in trackIDs:
        spots = tm.trackSpots(trackID)
    
        # Let's sort them by frame.
        ls = ArrayList(spots)
        #ls.sort(Spot.frameComparator)
        
        for spot in ls:
            values = [spot.ID(), trackID, spot.getFeature('FRAME'), \
                spot.getFeature('POSITION_X'), spot.getFeature('POSITION_Y'), spot.getFeature('POSITION_Z')]
            for i in range(nChannels):
                values.append(spot.getFeature('MEAN_INTENSITY%02d' % (i+1)))
                
            IJ.log(rowStr % tuple(values))
            l1 = (values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7])
            wr.writerow(l1)
    
    myfile.close()
    IJ.selectWindow(title)
    IJ.run("Close")

    
od = OpenDialog("Time Laps Images", "")
firstDir = od.getDirectory()
fileList = os.listdir(firstDir)

if "DisplaySettings.json" in fileList:
    fileList.remove("DisplaySettings.json")
if ".DS_Store" in fileList:  
    fileList.remove(".DS_Store")  
#print(firstDir + fileList[0])

totalCount = []
i = 1
for fileName in fileList:
    currentFile = firstDir + fileName
    print(firstDir)
    #IJ.run("Bio-Formats Importer", "open=[" + currentFile + "] color_mode=Default split_channels view=Hyperstack stack_order=XYCZT series_list="+str(i))
    #IJ.run("Bio-Formats Importer", "open=[" + currentFile + "] color_mode=Composite view=Hyperstack stack_order=XYCZT use_virtual_stack")
    #IJ.run("Set Measurements...", "area limit redirect=None decimal=0")
    imp = IJ.openImage(currentFile)
    imp.show()
    track()
    

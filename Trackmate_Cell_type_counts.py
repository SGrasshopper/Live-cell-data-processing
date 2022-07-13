from fiji.plugin.trackmate.detection import LogDetectorFactory
from fiji.plugin.trackmate.features.spot import SpotContrastAndSNRAnalyzerFactory
import fiji.plugin.trackmate.tracking.sparselap.SparseLAPTrackerFactory as SparseLAPTrackerFactory
from fiji.plugin.trackmate.tracking.sparselap import SparseLAPTrackerFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.tracking import LAPUtils
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import fiji.plugin.trackmate.features.track.TrackDurationAnalyzer as TrackDurationAnalyzer
import fiji.plugin.trackmate.features.track.TrackSpotQualityFeatureAnalyzer as TrackSpotQualityFeatureAnalyzer
import fiji.plugin.trackmate.SelectionModel as SelectionModel
import fiji.plugin.trackmate.Settings as Settings
import fiji.plugin.trackmate.Model as Model
import fiji.plugin.trackmate.TrackMate as TrackMate
import fiji.plugin.trackmate.Spot as Spot
import fiji.plugin.trackmate.TrackMate
from ij.plugin import ChannelSplitter
from ij.plugin import ImageCalculator
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
from ij import ImagePlus

#IJ.run("Stack to Hyperstack...", "order=xyczt(default) channels=2 slices=1 frames=45 display=Color");
 
imp5 = IJ.getImage()
IJ.run("Re-order Hyperstack ...", "channels=[Channels (c)] slices=[Frames (t)] frames=[Slices (z)]")
imp5 = IJ.getImage()
orgtitle = imp5.getTitle()
    
nChannels = imp5.getNChannels()
# Setup settings for TrackMate
settings = Settings(imp5)

# Spot analyzer: we want the multi-C intensity analyzer.
settings.addAllAnalyzers() 

# Spot detector.
settings.detectorFactory = LogDetectorFactory()
settings.detectorSettings = settings.detectorFactory.getDefaultSettings()
settings.detectorSettings['TARGET_CHANNEL'] = 2
settings.detectorSettings['RADIUS'] = 2.2
settings.detectorSettings['THRESHOLD'] = 25.0

# Spot tracker.
# Configure tracker - We don't want to allow merges or splits
settings.trackerFactory = SparseLAPTrackerFactory()
settings.trackerSettings = LAPUtils.getDefaultLAPSettingsMap() # almost good enough
settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = False
settings.trackerSettings['ALLOW_TRACK_MERGING'] = False
settings.trackerSettings['LINKING_MAX_DISTANCE'] = 0.5
settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = 0.5
settings.trackerSettings['MAX_FRAME_GAP'] = 1

# Configure track filters
settings.addTrackAnalyzer(TrackDurationAnalyzer())
settings.addTrackAnalyzer(TrackSpotQualityFeatureAnalyzer())

filter1 = FeatureFilter('TRACK_DURATION', 4, True)
settings.addTrackFilter(filter1)

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

ds = DisplaySettingsIO.readUserDefault()
displayer =  HyperStackDisplayer(model, selectionModel, imp5, ds)
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
myfile = open('/Users/scottgrieshaber/Documents/'+orgtitle.split('.')[0]+'.csv', 'wb')
wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
wr.writerow(['Spot_ID', 'Track_ID', 'Frame', 'X', 'Y', 'Z', 'Channel_1', 'Channel_2', 'Channel_3'])

IJ.log('\n')
IJ.log(headerStr)
tm = model.getTrackModel()
trackIDs = tm.trackIDs(True)

for trackID in trackIDs:
    spots = tm.trackSpots(trackID)
    
    # Let's sort them by frame
    ls = ArrayList(spots)
    #ls.sort(Spot.frameComparator)
    
    for spot in ls:
        values = [spot.ID(), trackID, spot.getFeature('FRAME'), \
            spot.getFeature('POSITION_X'), spot.getFeature('POSITION_Y'), spot.getFeature('POSITION_Z')]
        
        for i in range(nChannels):
            IJ.log(str(i+1))
            #values.append(spot.getFeature('MEAN_INTENSITY%02d' % (i+1))
            values.append(spot.getFeature('MEAN_INTENSITY_CH{}'.format(i+1)))
            
        IJ.log(str(values))
        IJ.log(rowStr % tuple(values))
        l1 = (values[0], values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8])
        wr.writerow(l1)
myfile.close()
#IJ.selectWindow("Merged")
#IJ.run("Close")

import time
from pathlib import Path
startTime = time.time()

"""
##########################################################
User options
"""

#The aerial/satellite imagery to be posterised
inImage             = 'C:/GIS Work/SatelliteImage.tif'

#A polygon layer of modified land, to brighten urban/rural areas, leaving vegetation unbrightened
modifiedLandLayer   = 'C:/GIS Work/TasVegModified.gpkg'

#A layer of dark lines to split the segments (e.g contours)
darkLinesLayer      = 'C:/GIS Work/Contours.gpkg'

lightLinesLayer     = 'C:/GIS Work/LightLines.gpkg'

compressOptions     = 'COMPRESS=LZW|PREDICTOR=2|NUM_THREADS=8|BIGTIFF=IF_SAFER|TILED=YES'

"""
##########################################################
Set up some variables
"""

#Set up the layer name for the raster calculations
inImageName = inImage.split("/")
inImageName = inImageName[-1]
inImageName = inImageName[:len(inImageName)-4]
outImageName = inImageName

#Making a folder for processing
rootProcessDirectory = str(Path(inImage).parent.absolute()).replace('\\','/') + '/'
processDirectory = rootProcessDirectory + inImageName + 'SegmentProcess' + '/'
if not os.path.exists(processDirectory):        os.mkdir(processDirectory)

#Get attributes of the raster
inputRas = QgsRasterLayer(inImage) 
pixelSizeXInputRas = inputRas.rasterUnitsPerPixelX()
pixelSizeYInputRas = inputRas.rasterUnitsPerPixelY()
inputRasBounds = inputRas.extent() 
xminInputRas = inputRasBounds.xMinimum()
xmaxInputRas = inputRasBounds.xMaximum()
yminInputRas = inputRasBounds.yMinimum()
ymaxInputRas = inputRasBounds.yMaximum()
inputRasCrs = inputRas.crs().authid()
inputRasExtentParameter = str(xminInputRas) + ',' + str(xmaxInputRas) + ',' + str(yminInputRas) + ',' + str(ymaxInputRas) + ' [' + inputRasCrs + ']'

"""
##########################################################
Add in tasveg
"""

#Clip tasveg to the raster area
processing.run("native:extractbyextent", {'INPUT':modifiedLandLayer,'EXTENT':inputRasExtentParameter,'CLIP':True,'OUTPUT':processDirectory + 'ModifiedLandClipped.gpkg'})

#Create an addition raster with modified tasveg burnt in
processing.run("gdal:rasterize", {'INPUT':processDirectory + 'ModifiedLandClipped.gpkg','FIELD':'','BURN':40,'USE_Z':False,'UNITS':1,'WIDTH':pixelSizeXInputRas,'HEIGHT':pixelSizeYInputRas,'EXTENT':inputRasExtentParameter,
'NODATA':-1,'OPTIONS':compressOptions,'DATA_TYPE':1,'INIT':0,'INVERT':False,'EXTRA':'','OUTPUT':processDirectory + 'ModifiedLandClippedRasterised.tif'})

#Add the tasveg brightening to the raster
processing.run("gdal:rastercalculator", {'INPUT_A':inImage,'BAND_A':1,'INPUT_B':processDirectory + 'ModifiedLandClippedRasterised.tif','BAND_B':1,'INPUT_C':None,'BAND_C':None,'INPUT_D':None,'BAND_D':None,'INPUT_E':None,'BAND_E':None,'INPUT_F':None,'BAND_F':None,
    'FORMULA':'A+B','NO_DATA':None,'EXTENT_OPT':0,'PROJWIN':None,'RTYPE':4,'OPTIONS':compressOptions,'EXTRA':'','OUTPUT':processDirectory + 'ImageBand1CalcMod.tif'})
processing.run("gdal:rastercalculator", {'INPUT_A':inImage,'BAND_A':2,'INPUT_B':processDirectory + 'ModifiedLandClippedRasterised.tif','BAND_B':1,'INPUT_C':None,'BAND_C':None,'INPUT_D':None,'BAND_D':None,'INPUT_E':None,'BAND_E':None,'INPUT_F':None,'BAND_F':None,
    'FORMULA':'A+B','NO_DATA':None,'EXTENT_OPT':0,'PROJWIN':None,'RTYPE':4,'OPTIONS':compressOptions,'EXTRA':'','OUTPUT':processDirectory + 'ImageBand2CalcMod.tif'})
processing.run("gdal:rastercalculator", {'INPUT_A':inImage,'BAND_A':3,'INPUT_B':processDirectory + 'ModifiedLandClippedRasterised.tif','BAND_B':1,'INPUT_C':None,'BAND_C':None,'INPUT_D':None,'BAND_D':None,'INPUT_E':None,'BAND_E':None,'INPUT_F':None,'BAND_F':None,
    'FORMULA':'A+B','NO_DATA':None,'EXTENT_OPT':0,'PROJWIN':None,'RTYPE':4,'OPTIONS':compressOptions,'EXTRA':'','OUTPUT':processDirectory + 'ImageBand3CalcMod.tif'})

#Combine the bands
processing.run("gdal:buildvirtualraster", {'INPUT':[processDirectory + 'ImageBand1CalcMod.tif',processDirectory + 'ImageBand2CalcMod.tif',processDirectory + 'ImageBand3CalcMod.tif'],'RESOLUTION':0,'SEPARATE':True,'PROJ_DIFFERENCE':False,
    'ADD_ALPHA':False,'ASSIGN_CRS':None,'RESAMPLING':0,'SRC_NODATA':'','EXTRA':'','OUTPUT':processDirectory + '3BandModCombined.vrt'})

#Render out
processing.run("gdal:warpreproject", {'INPUT':processDirectory + '3BandModCombined.vrt','SOURCE_CRS':None,'TARGET_CRS':None,'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':None,'OPTIONS':compressOptions,'DATA_TYPE':0,'TARGET_EXTENT':None,
    'TARGET_EXTENT_CRS':None,'MULTITHREADING':True,'EXTRA':'','OUTPUT':processDirectory + '3BandModCombinedWarp.tif'})

"""
##########################################################
Dark line burning
"""

#Clip the dark line layer to the raster area
processing.run("native:extractbyextent", {'INPUT':darkLinesLayer,'EXTENT':inputRasExtentParameter,'CLIP':True,'OUTPUT':processDirectory + 'DarkLinesClipped.gpkg'})
processing.run("native:extractbyextent", {'INPUT':lightLinesLayer,'EXTENT':inputRasExtentParameter,'CLIP':True,'OUTPUT':processDirectory + 'LightLinesClipped.gpkg'})

#Create subtraction/addition rasters with the dark/light lines burnt in
processing.run("gdal:rasterize", {'INPUT':processDirectory + 'DarkLinesClipped.gpkg','FIELD':'','BURN':-15,'USE_Z':False,'UNITS':1,'WIDTH':pixelSizeXInputRas,'HEIGHT':pixelSizeYInputRas,'EXTENT':inputRasExtentParameter,
'NODATA':-1,'OPTIONS':compressOptions,'DATA_TYPE':1,'INIT':0,'INVERT':False,'EXTRA':'','OUTPUT':processDirectory + 'DarkLinesClippedRasterised.tif'})
processing.run("gdal:rasterize", {'INPUT':processDirectory + 'LightLinesClipped.gpkg','FIELD':'','BURN':20,'USE_Z':False,'UNITS':1,'WIDTH':pixelSizeXInputRas,'HEIGHT':pixelSizeYInputRas,'EXTENT':inputRasExtentParameter,
'NODATA':-1,'OPTIONS':compressOptions,'DATA_TYPE':1,'INIT':0,'INVERT':False,'EXTRA':'','OUTPUT':processDirectory + 'LightLinesClippedRasterised.tif'})

#Add the light and dark lines to what was calculated earlier
processing.run("gdal:rastercalculator", {'INPUT_A':processDirectory + 'ImageBand1CalcMod.tif','BAND_A':1,'INPUT_B':processDirectory + 'DarkLinesClippedRasterised.tif','BAND_B':1,
    'INPUT_C':processDirectory + 'LightLinesClippedRasterised.tif','BAND_C':1,'INPUT_D':None,'BAND_D':None,'INPUT_E':None,'BAND_E':None,'INPUT_F':None,'BAND_F':None,
    'FORMULA':'A+B+C','NO_DATA':None,'EXTENT_OPT':0,'PROJWIN':None,'RTYPE':4,'OPTIONS':compressOptions,'EXTRA':'','OUTPUT':processDirectory + 'ImageBand1CalcAll.tif'})
processing.run("gdal:rastercalculator", {'INPUT_A':processDirectory + 'ImageBand2CalcMod.tif','BAND_A':1,'INPUT_B':processDirectory + 'DarkLinesClippedRasterised.tif','BAND_B':1,
    'INPUT_C':processDirectory + 'LightLinesClippedRasterised.tif','BAND_C':1,'INPUT_D':None,'BAND_D':None,'INPUT_E':None,'BAND_E':None,'INPUT_F':None,'BAND_F':None,
    'FORMULA':'A+B+C','NO_DATA':None,'EXTENT_OPT':0,'PROJWIN':None,'RTYPE':4,'OPTIONS':compressOptions,'EXTRA':'','OUTPUT':processDirectory + 'ImageBand2CalcAll.tif'})
processing.run("gdal:rastercalculator", {'INPUT_A':processDirectory + 'ImageBand3CalcMod.tif','BAND_A':1,'INPUT_B':processDirectory + 'DarkLinesClippedRasterised.tif','BAND_B':1,
    'INPUT_C':processDirectory + 'LightLinesClippedRasterised.tif','BAND_C':1,'INPUT_D':None,'BAND_D':None,'INPUT_E':None,'BAND_E':None,'INPUT_F':None,'BAND_F':None,
    'FORMULA':'A+B+C','NO_DATA':None,'EXTENT_OPT':0,'PROJWIN':None,'RTYPE':4,'OPTIONS':compressOptions,'EXTRA':'','OUTPUT':processDirectory + 'ImageBand3CalcAll.tif'})

#Combine the bands
processing.run("gdal:buildvirtualraster", {'INPUT':[processDirectory + 'ImageBand1CalcAll.tif',processDirectory + 'ImageBand2CalcAll.tif',processDirectory + 'ImageBand3CalcAll.tif'],'RESOLUTION':0,'SEPARATE':True,'PROJ_DIFFERENCE':False,
    'ADD_ALPHA':False,'ASSIGN_CRS':None,'RESAMPLING':0,'SRC_NODATA':'','EXTRA':'','OUTPUT':processDirectory + '3BandAllCombined.vrt'})

#Render out
processing.run("gdal:warpreproject", {'INPUT':processDirectory + '3BandAllCombined.vrt','SOURCE_CRS':None,'TARGET_CRS':None,'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':None,'OPTIONS':compressOptions,'DATA_TYPE':0,'TARGET_EXTENT':None,
    'TARGET_EXTENT_CRS':None,'MULTITHREADING':True,'EXTRA':'','OUTPUT':processDirectory + '3BandAllCombinedWarp.tif'})

"""
##########################################################
Segmentation
"""

#Segment the raster first to determine which areas have poor 'goodness' with the resulting segments
processing.run("grass7:i.segment", {'input':[processDirectory + '3BandAllCombinedWarp.tif'],'threshold':0.22,'method':0,'similarity':0,'minsize':500,'memory':4000,'iterations':10,'seeds':None,'bounds':None,'-d':False,'-w':False,
    'output':processDirectory + '3BandAllCombinedWarpSegment.tif','goodness':processDirectory + '3BandAllCombinedWarpGoodness.tif','GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})

#Resample the goodness out then in to remove noise
processing.run("gdal:warpreproject", {'INPUT':processDirectory + '3BandAllCombinedWarpGoodness.tif','SOURCE_CRS':None,'TARGET_CRS':None,'RESAMPLING':3,'NODATA':0,'TARGET_RESOLUTION':pixelSizeXInputRas * 4,'OPTIONS':compressOptions,'DATA_TYPE':0,
    'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':True,'EXTRA':'','OUTPUT':processDirectory + '3BandAllCombinedWarpGoodnessResamp.tif'})
processing.run("gdal:warpreproject", {'INPUT':processDirectory + '3BandAllCombinedWarpGoodnessResamp.tif','SOURCE_CRS':None,'TARGET_CRS':None,'RESAMPLING':3,'NODATA':0,'TARGET_RESOLUTION':pixelSizeXInputRas,'OPTIONS':compressOptions,'DATA_TYPE':0,
    'TARGET_EXTENT':inputRasExtentParameter,'TARGET_EXTENT_CRS':None,'MULTITHREADING':True,'EXTRA':'','OUTPUT':processDirectory + '3BandAllCombinedWarpGoodnessResampResamp.tif'})

#Classify the raster so that anywhere that has a goodness below 0.98 is a seed for the next segmentation
processing.run("gdal:rastercalculator", {'INPUT_A':processDirectory + '3BandAllCombinedWarpGoodnessResampResamp.tif','BAND_A':1,'INPUT_B':None,'BAND_B':None,'INPUT_C':None,'BAND_C':None,'INPUT_D':None,'BAND_D':None,'INPUT_E':None,'BAND_E':None,'INPUT_F':None,'BAND_F':None,
    'FORMULA':'A < 0.98','NO_DATA':0,'EXTENT_OPT':0,'PROJWIN':None,'RTYPE':0,'OPTIONS':compressOptions,'EXTRA':'','OUTPUT':processDirectory + '3BandAllCombinedWarpGoodnessResampResampClassed.tif'})

#Segement again with the seeds
processing.run("grass7:i.segment", {'input':[processDirectory + '3BandAllCombinedWarp.tif'],'threshold':0.22,'method':0,'similarity':0,'minsize':250,'memory':4000,'iterations':15,
    'seeds':processDirectory + '3BandAllCombinedWarpGoodnessResampResampClassed.tif','bounds':None,'-d':False,'-w':False,'output':processDirectory + '3BandAllCombinedWarpSegmentP2.tif','goodness':processDirectory + '3BandAllCombinedWarpGoodnessP2.tif',
    'GRASS_REGION_PARAMETER':None,'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'','GRASS_RASTER_FORMAT_META':''})

"""
##########################################################
Sample rgb values
"""

#Convert the segments to polgyons
processing.run("gdal:polygonize", {'INPUT':processDirectory + '3BandAllCombinedWarpSegmentP2.tif','BAND':1,'FIELD':'DN','EIGHT_CONNECTEDNESS':False,'EXTRA':'','OUTPUT':processDirectory + '3BandAllCombinedWarpSegmentP2Polygon.gpkg'})

#Get the median rgb values from the raster + tasveg
processing.run("native:zonalstatisticsfb", {'INPUT':processDirectory + '3BandAllCombinedWarpSegmentP2Polygon.gpkg','INPUT_RASTER':processDirectory + '3BandModCombinedWarp.tif','RASTER_BAND':1,'COLUMN_PREFIX':'_','STATISTICS':[3],'OUTPUT':processDirectory + 'RedMedian.gpkg'})
processing.run("native:zonalstatisticsfb", {'INPUT':processDirectory + '3BandAllCombinedWarpSegmentP2Polygon.gpkg','INPUT_RASTER':processDirectory + '3BandModCombinedWarp.tif','RASTER_BAND':2,'COLUMN_PREFIX':'_','STATISTICS':[3],'OUTPUT':processDirectory + 'GreenMedian.gpkg'})
processing.run("native:zonalstatisticsfb", {'INPUT':processDirectory + '3BandAllCombinedWarpSegmentP2Polygon.gpkg','INPUT_RASTER':processDirectory + '3BandModCombinedWarp.tif','RASTER_BAND':3,'COLUMN_PREFIX':'_','STATISTICS':[3],'OUTPUT':processDirectory + 'BlueMedian.gpkg'})

#Convert this to raster bands
processing.run("gdal:rasterize_over", {'INPUT':processDirectory + 'RedMedian.gpkg','INPUT_RASTER':processDirectory + 'ImageBand1CalcAll.tif','FIELD':'_median','ADD':False,'EXTRA':''})
processing.run("gdal:rasterize_over", {'INPUT':processDirectory + 'GreenMedian.gpkg','INPUT_RASTER':processDirectory + 'ImageBand2CalcAll.tif','FIELD':'_median','ADD':False,'EXTRA':''})
processing.run("gdal:rasterize_over", {'INPUT':processDirectory + 'BlueMedian.gpkg','INPUT_RASTER':processDirectory + 'ImageBand3CalcAll.tif','FIELD':'_median','ADD':False,'EXTRA':''})

#Combine the bands
processing.run("gdal:buildvirtualraster", {'INPUT':[processDirectory + 'ImageBand1CalcAll.tif',processDirectory + 'ImageBand2CalcAll.tif',processDirectory + 'ImageBand3CalcAll.tif'],'RESOLUTION':0,'SEPARATE':True,
    'PROJ_DIFFERENCE':False,'ADD_ALPHA':False,'ASSIGN_CRS':None,'RESAMPLING':0,'SRC_NODATA':'','EXTRA':'','OUTPUT':processDirectory + 'VirtualFinal.vrt'})
    
processing.run("gdal:warpreproject", {'INPUT':processDirectory + 'VirtualFinal.vrt','SOURCE_CRS':None,'TARGET_CRS':None,'RESAMPLING':None,'NODATA':None,'TARGET_RESOLUTION':None,'OPTIONS':compressOptions,'DATA_TYPE':1,
    'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':True,'EXTRA':'','OUTPUT':processDirectory + inImageName + 'Posterised.tif'})


"""
#######################################################################
"""

#All done
endTime = time.time()
totalTime = endTime - startTime
print("Done, this took " + str(int(totalTime)) + " seconds")



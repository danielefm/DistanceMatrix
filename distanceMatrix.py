import googlemaps
import numpy as np
import ogr, gdal
import pandas as pd
from random import randint
import datetime
import os

nextWedYear= 2020
nextWedMonth= 4
nextWedDay= 8

shapeFile = "Macrozonas_DF_2016.shp"

loc_csv1 = pd.read_csv("origins.csv",sep=';')
loc_csv2 = pd.read_csv("destinations.csv",sep=';')
origin=loc_csv1["origin"].tolist()
destination=loc_csv2["destination"].tolist()

modes = ['driving','walking','bicycling','transit']

def randomPoint(file, region):
    polygon_fn = file

    # Define pixel_size which equals distance betweens points
    pixel_size = 0.003

    # Open the data source and read in the extent
    source_ds = ogr.Open(polygon_fn)
    source_layer = source_ds.GetLayer()
    source_layer.SetAttributeFilter("RA_NOME='"+region+"'")
    x_min, x_max, y_min, y_max = source_layer.GetExtent()

    # Create the destination data source
    x_res = int((x_max - x_min) / pixel_size)
    y_res = int((y_max - y_min) / pixel_size)
    target_ds = gdal.GetDriverByName('GTiff').Create('temp.tif', x_res, y_res, gdal.GDT_Byte)
    target_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(255)

    # Rasterize
    gdal.RasterizeLayer(target_ds, [1], source_layer, burn_values=[1])

    # Read as array
    array = band.ReadAsArray()

    raster = gdal.Open('temp.tif')
    geotransform = raster.GetGeoTransform()

    # Convert array to point coordinates
    count = 0
    roadList = np.where(array == 1)
    multipoint = ogr.Geometry(ogr.wkbMultiPoint)
    for indexY in roadList[0]:
        indexX = roadList[1][count]
        geotransform = raster.GetGeoTransform()
        originX = geotransform[0]
        originY = geotransform[3]
        pixelWidth = geotransform[1]
        pixelHeight = geotransform[5]
        Xcoord = originX+pixelWidth*indexX
        Ycoord = originY+pixelHeight*indexY
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(Xcoord, Ycoord)
        multipoint.AddGeometry(point)
        count += 1

    # Remove temporary files
    os.remove('temp.tif')

    i = randint(0,multipoint.GetGeometryCount()-1)
    point = multipoint.GetGeometryRef(i)
    coord = (point.GetY(),point.GetX())

    return coord

def commuteTime(fromPlace, toPlace, how, year, month, day):
    when = (datetime.date(year,month,day)-datetime.date(1970,1,1)).total_seconds()+28800
    gmaps = googlemaps.Client(key="AIzaSyDX9GTh5B0jDjsZ0fVe_owr1vBRoO6Yblg")
    result_matrix = gmaps.distance_matrix(origins=fromPlace,destinations=toPlace,mode=how,departure_time=when)
    if result_matrix['rows'][0]['elements'][0]['status']=='OK':
        return result_matrix['rows'][0]['elements'][0]['duration']['value']
    else: return -1

for mode in modes:
    df = pd.DataFrame(index=origin,columns=destination)
    for o in origin:
        for d in destination:
            sum=0
            counts=0
            for i in [0,1,2]:
                pointOrigin = randomPoint(shapeFile, o)
                pointDestination = randomPoint(shapeFile, d)
                duration=commuteTime(pointOrigin,pointDestination,mode,nextWedYear,nextWedMonth,nextWedDay)
                if duration!=-1:
                    sum=sum+duration
                    counts=counts+1
            if counts!=0:
               df.loc[o,d]=sum/counts
            else:
                df.loc[o,d]=-1
    df.to_csv("mode"+mode+".csv")
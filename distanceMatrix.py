import datetime
import os
from random import randint

import gdal
import googlemaps
import numpy as np
import ogr
import pandas as pd


GOOGLE_KEY = "insert API KEY"

# We will make requests to Google Maps API that use traffic information
# because we need to know the travel duration on a specific time of a
# typical weekday. However, Google Maps only allows us to make requests
# considering future times. Therefore, here we have to specify year,
# month and day of the next typical Wednesday.

year_of_next_wednesday= 2020
month_of_next_wednesday= 4
day_of_next_wednesday= 8

shp_file = "Brasilia_DF_2016.shp"

origin = pd.read_csv("origins.csv", sep=';')["origin"].tolist()
destination = pd.read_csv("destinations.csv", 
                          sep=';')["destination"].tolist()

modes = ['driving', 'walking', 'bicycling', 'transit']


def randomPoint(file, region):

    """ Returns a random point P = (X, Y) that lies within the area of
    a poligon defined by the feature name "region" that is parte of
    "file", which is an ESRI Shapefile type document.
    """
    
    # Define pixel_size which equals distance betweens points
    pixel_size = 0.003

    # Open the data source and read in the extent
    source_shapefile = ogr.Open(file)
    source_layer = source_shapefile.GetLayer()
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

    # Choose a random point
    i = randint(0,multipoint.GetGeometryCount()-1)
    point = multipoint.GetGeometryRef(i)
    coord = (point.GetY(),point.GetX())

    return coord


def commuteTime(fromPlace, toPlace, how, year, month, day):
    
    """ Returns the duration of a trip between two points (fromPlace),
    given a specific transportation mode (how: 'driving','walking',
    'bicycling', 'transit'), at 8 a.m. of the given day.
    Returns -1 if there is no route found between the points, using
    the given mode.
    """

    # In order to make a Google Maps API request, we have to specify
    # the departure time as seconds since midnight, January 1, 1970.
    # Therefore, we use the datetime library to calculate the time
    # difference between the desired request day and 01/01/1970.
    # At the end, we sum up 28800 because our request is at 8 a.m.,
    # and there are 28000 seconds from midnight to 8 a.m.
    
    when = (datetime.date(year,month,day) 
           - datetime.date(1970,1,1)).total_seconds()
           + 28800
    
    gmaps = googlemaps.Client(key=GOOGLE_KEY)
    
    result_matrix = gmaps.distance_matrix(origins = fromPlace,
                                          destinations=toPlace,
                                          mode=how,
                                          departure_time=when)

    if result_matrix['rows'][0]['elements'][0]['status']=='OK':
    
        return result_matrix['rows'][0]['elements'][0]['duration']['value']
    
    else: return -1


for mode in modes:

    df = pd.DataFrame(index=origin, columns=destination)
    for o in origin:
        for d in destination:
            sum=0
            counts=0
            for i in [0, 1, 2]:
                pointOrigin = randomPoint(shp_file, o)
                pointDestination = randomPoint(shp_file, d)
                duration=commuteTime(pointOrigin,
                                     pointDestination,
                                     mode,
                                     year_of_next_wednesday,
                                     month_of_next_wednesday,
                                     day_of_next_wednesday)

                if duration!=-1:
                    sum=sum+duration
                    counts=counts+1

            if counts!=0:
               df.loc[o,d]=sum/counts
            else:
                df.loc[o,d]=-1
                
    df.to_csv("mode"+mode+".csv")
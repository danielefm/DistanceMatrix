# DistanceMatrix
Using Python, GDAL and Google Maps API to calculate travel times between pairs of regions, given an specific weekday and time.

## What problem are we trying to solve?
Given a specific region, divided into administrative areas, we want to calculate the average time a person takes to go from an area to another, at 8 a.m. of a typical weekday, for each transportation mode available (e.g.: driving, taking public transport, walking, bicycling). 

## What is the result we expect?
After doing this for all possible pairs of regions, for each mode, we want to obtain a Distance Matrix, which presents the average trip duration for the pairs of origins and destinations.

## Why do we want to do this?
This information is required as a feature for a machine learning model that predicts a person transportation behavior, as we can read from the article "Data-driven activity scheduler for agent-based mobility models", https://www.sciencedirect.com/science/article/pii/S0968090X18306417.

## How do we do this?
The example we present here comprises the metropolitan area of Brasilia, Brazil, but may be replicated using diferent input files.

### Input files
* An ESRI Shapefile set of documents (.shp + .shx + .cpj + .dbf + .prj + .qpj), in which the polygon layer is formed by features representing the administrative areas, which names are presented in a field. In this example, we use a Shapefile with information about the Brasilia Metropolitan Area, composed by the 31 administrative areas (or neighborhoods) of Brasilia and 21 towns.
* An "origins.csv" file and an "destinations.csv" file, which are lists with the name of the regions that must be included as origins and destinations on the Distance Matrix.

### Algorithm design considerations
* We define a randomPoint function that converts the Shapefile polygon into points and then returns one of the points' coordinates (it was based on the recipe as in https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#convert-polygon-to-points);
* We define a commuteTime function that returns the trip duration between to points, given a day and a transportation mode, using the Google Maps API;
* Finally, we apply the randomPoint funcion to select origin and destination points for each pair of administrative regions and use them as input to the commuteTime function. We calculate the commuteTime for three pairs of points, for each pair of administrative regions, and fill in the Distance Matrix instance with the average of those values.

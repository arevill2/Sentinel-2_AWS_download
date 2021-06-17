# run with python3 
# pip3 install sentinelhub pandas json shapely matplotlib seaborn 
from sentinelhub import WebFeatureService, BBox, CRS, DataSource, SHConfig, AwsTileRequest,AwsTile,get_area_info
from sentinelhub import BBoxSplitter, OsmSplitter, TileSplitter, CustomGridSplitter, UtmZoneSplitter, UtmGridSplitter
import pandas as pd 
import numpy as np 
import json
from shapely.geometry import shape, Point
import datetime
import glob
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as plt_polygon
import os 

from datetime import datetime

#from TOA2LAI_S2 import AC_LAI


# %reload_ext autoreload
# %autoreload 2
# %matplotl inlin Sne
# 
"""\
Use sentinelhub to query AWS for S2 L2A data 
Filter images found and download 
""" 

###############################################################################################################################

INSTANCE_ID = ''  # In case you put instance ID into configuration file you can leave this unchanged

if INSTANCE_ID:
	config = SHConfig()
	config.instance_id = INSTANCE_ID
else:
	config = None

###############################################################################################################################

def get_s2_scenes(geojason_file):
       with open('C:/Users/arevi/OneDrive/BBSRC_IAA_project/spatial_data/'+geojason_file) as f: js = json.load(f) # a geojson of the field 
       
       for feature in js['features']: polygon = shape(feature['geometry'])
       bbox_splitter = BBoxSplitter([polygon], CRS.WGS84, (5,5))  # bounding box will be split into grid of 5x5 boudning boxes - needed to finr the correct tiles (don't know why but works this way)
       search_bbox = bbox_splitter
       
       dateTimeObj = datetime.now()
       timestampStr = dateTimeObj.strftime("%Y-%m-%dT%H:%M:%S")
       
       search_time_interval = ('2020-11-01T00:00:00',timestampStr) # from , to dates 
       
       ### this block queries AWS for the data 
       datainfo = pd.DataFrame(columns=['productIdentifier','tilecode','completionDate'])
       
       for tile_info in get_area_info(bbox_splitter.get_bbox_list()[0], search_time_interval, maxcc=0.66):
       	datainfo = datainfo.append({'productIdentifier': tile_info['properties']['productIdentifier'],
       								'tilecode' : tile_info['properties']['title'][49:55],
       								'completionDate': tile_info['properties']['completionDate'][:10]}, ignore_index=True)
       
       ### collect metadata 
       for i in range(len(datainfo)):
       	try:
       		tile_id = datainfo.productIdentifier[i]
       		tile_name, time, aws_index = AwsTile.tile_id_to_tile(tile_id)
       		request = AwsTileRequest(
       			tile = tile_name,
       			time = time,
       			aws_index = aws_index,
       			bands=[''],
       			metafiles = ['tileInfo'],
       			data_collection = DataSource.SENTINEL2_L2A) # change this to a differnt collection if you want unprocessed data 
       		infos = request.get_data() 
       		#datainfo['datacoveragepct'][datainfo.productIdentifier == datainfo.productIdentifier[i]] = infos[0]['dataCoveragePercentage']
       		#datainfo['cloudpixelpct'][datainfo.productIdentifier == datainfo.productIdentifier[i]] = infos[0]['cloudyPixelPercentage']
       	except : pass 
       
       ### check the results of the query and the metadata downloaded just above 
       ### and ensure that you dont download scenes that are e.g. 90% above ocean or too cloudy
       ### this block is more for UK wide scenes downloading 
       #datainfo = datainfo[datainfo.datacoveragepct > 25] # EDIT : keep scenes in which land area covers > 25% of the scence
       #datainfo = datainfo[datainfo.cloudpixelpct < 50]  # EDIT : keep scenes in which cloud coverage < 50% 
       #datainfo = datainfo.dropna(subset=['datacoveragepct','datacoveragepct'])
       datainfo.index = np.arange(0,len(datainfo))
       
       # print ('process #2 : ' + str(len(datainfo)))
       
       
       # ### the codes of available bands and resolutions (10m,20m,60m) - saves time, space and £ to select only the ones you need
       # # bands_list = [R10m/B02', 'R10m/B03', 'R10m/B04', 'R10m/B08', 'R10m/AOT', 'R10m/TCI', 'R10m/WVP',
       # # 'R20m/B02', 'R20m/B03', 'R20m/B04', 'R20m/B05', 'R20m/B06', 'R20m/B07', 'R20m/B8A', 'R20m/B11', 'R20m/B12', 'R20m/AOT', 'R20m/SCL', 'R20m/TCI', 'R20m/VIS', 'R20m/WVP', 
       # # 'R60m/B01', 'R60m/B02', 'R60m/B03', 'R60m/B04', 'R60m/B05', 'R60m/B06', 'R60m/B07', 'R60m/B8A', 'R60m/B09', 'R60m/B11', 'R60m/B12', 'R60m/AOT', 'R60m/SCL', 'R60m/TCI', 'R60m/WVP']
   
       def get_band_name(file):
       	file_date = ((file.split("/")[7]).split("_")[3]).split("T")
       	return file_date
       
       ### donwnload complete folders
       for i in range(len(set(datainfo.tilecode))):
       	datainfosub = datainfo[datainfo.tilecode == list(set(datainfo.tilecode))[i]]
       	out_directory = 'C:/Users/arevi/OneDrive/BBSRC_IAA_project/LAI_estimates/s2_aws_download/'+str(datainfo.tilecode[i])
       	file_folders = (glob.glob(out_directory+'/*'))
       	existing_s2 = [list(b) for b in zip(*map(get_band_name, file_folders))][0]
       	print (str(list(set(datainfo.tilecode))[i]))
       	for ii in range(len(datainfosub)):
       		date_text = (datainfosub.productIdentifier[ii].split(sep="_")[6]).split(sep="T")[0]     
       		
       		if date_text in existing_s2:
       			print('existing ' + datainfosub.productIdentifier[ii])
       			continue
       		else:
       		
       			datainfosub.productIdentifier.iloc[ii]
       			try:
       				tile_id = datainfosub.productIdentifier.iloc[ii]
       				tile_name, time, aws_index = AwsTile.tile_id_to_tile(tile_id)
       				request = AwsTileRequest(
       					tile = tile_name,
       					time = time,
       					aws_index = aws_index,
       					bands=['R20m/B02', 'R20m/B03', 'R20m/B04', 'R20m/B05', 'R20m/B06', 'R20m/B07', 'R20m/B8A', 'R20m/B11', 'R20m/B12', 'R20m/AOT', 'R20m/SCL', 'R20m/TCI', 'R20m/VIS', 'R20m/WVP'],
       					data_folder = 'C:/Users/arevi/OneDrive/BBSRC_IAA_project/LAI_estimates/s2_aws_download/%s' % str(list(set(datainfo.tilecode))[i]),
       					data_collection = DataSource.SENTINEL2_L2A, # change this to a differnt collection if you want unprocessed data 
       					safe_format = True)
       				request.save_data() 
       			except : pass
       return  

# MilborneStAndrews
get_s2_scenes('MilborneStAndrews.geojson')

# West Fortune
#get_s2_scenes('map.geojson')
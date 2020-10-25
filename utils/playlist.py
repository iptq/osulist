import pymongo
import os
import time
from dotenv import load_dotenv, find_dotenv
from .html_utils import html_a_blank_format, html_a_format, html_delete_format
from .time_utils import time_format_num, time_format_str

import time
# load environment variables
load_dotenv( find_dotenv() )
MONGO_USER = os.getenv( 'MONGO_USER_PUBLIC' )
MONGO_PASSWORD = os.getenv( 'MONGO_PASSWORD_PUBLIC' )
MONGO_CLUSTER = os.getenv( 'MONGO_CLUSTER' )
OSU_TOKEN = os.getenv( 'OSU_TOKEN' )

# common URLs
osu_beatmap_url = "https://osu.ppy.sh/b/"
osu_mirror_url = "https://beatconnect.io/b/" # needs to be followed by beatmapset_id
osu_direct_url = "osu://b/" # needs to be followed by beatmap_id
osu_preview_url = "https://b.ppy.sh/preview/"


class Playlist():
	""" class defintion for a single playlist object
		- one playlist is saved as a single collection within the 'osu_maps' database in MongoDB
		- provides methods to fetch data from MongoDB and format it into usable data for the website
		- requires database > collection to be initialized
	""" 
	def __init__( self, db, collection ):
		self.db = db
		self.collection = collection
		self.mongo_client_str = "mongodb+srv://{}:{}@{}.mongodb.net/{}?retryWrites=true&w=majority".format( MONGO_USER, MONGO_PASSWORD, MONGO_CLUSTER, self.db )
		self.map_data = self.fetch_maps()
		self.playlist_details = self.fetch_details()
		#print( "Playlist details:", self.playlist_details )

	def client( self ):
		return pymongo.MongoClient( self.mongo_client_str )[self.db][self.collection]

	# get map playlist data from mongodb
	def fetch_maps( self ):
		client = self.client()
		data = client.find( { 'beatmap_id': { '$exists': True } } )
		return list( data )

	# get map playlist data from mongodb
	def fetch_details( self ):
		client = pymongo.MongoClient( self.mongo_client_str )['playlist_details']['details']
		data = client.find( { 'playlist_id': self.collection } )
		return list( data )

	def add_map( self, beatmap_id ):
		try:
			beatmap_id = beatmap_id.split('/')[5].strip()
			if beatmap_id :
				pass
		except:
			raise("fucked lmao")

	def delete_map( self, user_id, beatmap_id ):
		# remove map
		client = self.client()
		client.delete_one( { 'beatmap_id': beatmap_id } )

		# update playlist details
		client = pymongo.MongoClient( self.mongo_client_str )['playlist_details']['details']
		client.update_one( { 'playlist_id': self.collection }, { '$set': { 'playlist_size': self.get_size() - 1 } } )

	# get columns for display in playlist pages
	def get_columns( self ):
		return [{
			'data': 'position',
			'title': '#'
		}, {
			'data': 'beatmap_id',
			'title': 'beatmap_id',
			'visible': False
		}, {
			'data': 'title',
			'title': 'Beatmap'
		}, {
			'data': 'creator',
			'title': 'Creator'
		}, {
			'data': 'bpm',
			'title': 'BPM'
		}, {
			'data': 'sr',
			'title': 'SR'
		}, {
			'data': 'length',
			'title': 'Length'
		}, {
			'data': 'cs',
			'title': 'CS',
			'visible': False
		}, {
			'data': 'ar',
			'title': 'AR',
			'visible': False
		}, {
			'data': 'tags',
			'title': 'Tags',
			'visible': False
		}, {
			'data': 'mirror',
			'title': '',
			'sortable': False
		}, {
			'data': 'direct',
			'title': '',
			'sortable': False
		}, {
			'data': 'delete',
			'title': '',
			'sortable': False
		}]

	# format mongodb map data into well-formatted dict for bootstrap-tables
	def get_rows( self ):
		table_data = []
		position = 1

		for x in self.get_raw_map_data():
			table_data.append({
				'position': position,
				'beatmap_id': x['beatmap_id'],
				'title': html_a_format( osu_beatmap_url + x['beatmap_id'] , f"{x['artist']} - {x['title']} [{x['version']}]" ),
				'creator': x['creator'],
				'bpm': round( float( x['bpm'] ) ),
				'sr': f"{round( float(x['difficultyrating']), 2)}&nbsp;&#9733;",
				'length': f"{time_format_num( x['total_length'] )} ({time_format_num( x['hit_length'] )})",
				'cs': x['diff_size'],
				'ar': x['diff_approach'],
				'tags': x['tags'],
				'mirror': html_a_format( osu_mirror_url + x['beatmapset_id'] , "mirror" ),
				'direct': html_a_format( osu_direct_url + x['beatmap_id'] , "direct" ),
				'delete': html_delete_format( '/delete_map', self.collection, self.get_details()['playlist_creator_id'], x['beatmap_id'], "delete" )
			})
			position += 1
		return table_data

	# get playlist details such as playlist title, description, creator, etc
	def get_details( self ):
		return self.playlist_details[0]

	# return total duration of all beatmaps in a playlist
	def get_duration( self ):
		pl_total_length = sum( [ int( x['total_length'] ) for x in self.get_raw_map_data() ] )
		pl_hit_length = sum( [ int( x['hit_length'] ) for x in self.get_raw_map_data() ] )
		return f"{time_format_str( pl_total_length )} ({time_format_str( pl_hit_length )})"

	# return number of maps in playlist
	def get_size( self ):
		return len( self.get_raw_map_data() )

	# return raw data from mongodb collection
	def get_raw_map_data( self ):
		return self.map_data
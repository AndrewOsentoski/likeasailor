import os
from flask import Flask, render_template, make_response, request
import pandas as pd
import urllib.request
import json
from bs4 import BeautifulSoup
import pandas as pd
import base64
import requests
import re


class Song(object):

	def __init__ (self, name, artist, lyrics = None, swears = None, swearwords = None, perfectmatch = None):
		self.name = name
		self.artist = artist
		if lyrics is None:
			lyrics = []
		self.lyrics = lyrics
		if swears is None:
			self.swears = False
		self.swears = swears
		if swearwords is None:
			swearwords = []
		self.swearwords = swearwords
		if perfectmatch is None:
			perfectmatch = False
		self.perfectmatch = perfectmatch
		
		self.lyrics = self.getLyrics()
		self.swears, self.swearwords = self.checkForSwears()
		
		
	def printThing(self):
		print('Song: %s' % (self.name))
		print('Artist: %s' % (self.artist))
		print('Swears: %s' % (self.swears))
		if len(self.swearwords)!=0:
			print('Swear words: ')
			for swear in self.swearwords:
				print('> %s' % (swear))
		print('Found Perfect Match: %s \n' % (self.perfectmatch))
		
	def getLyrics(self):
		name = self.name
		artist = self.artist
		lyrics = []
		lyrics1 = []
		lyrics2 = []
		header = {
		'User-Agent' : 'LikeASailor',
		'Accept' : 'application/json',
		'Host' : 'api.genius.com',
		'Authorization' : 'Bearer %s' % ('rqoeLIBcaU4F3Wb5EReoL4AZV9Q0DJD_t0Ultk-g2fqRTg_uSLqULIwIck0RPNsU')
		}
		
		baseURL = 'http://api.genius.com/search?q='
		pattern = '\(.+|\[.+|\s\(.+|\s\[.+'
		songLow = name.lower()
		songMatch = re.sub(pattern, "", songLow)
		songSearch = songMatch.replace(" ", "%20")
		artistLow = artist.lower()
		artistSearch = artistLow.replace(" ", "%20")
		
		req = urllib.request.Request(baseURL+artistSearch+"%20"+songSearch, headers = header)
		req2 = urllib.request.urlopen(req)
		string = req2.read().decode('utf-8')
		jsono = json.loads(string)
		mainDict = {}
		
		
				
		for songDict in jsono['response']['hits']:
			if songDict['result']['title'].lower() == songLow and songDict['result']['primary_artist']['name'].lower() == artistLow:
				mainDict = songDict['result']
				self.perfectmatch = True
				break
			elif songDict['result']['title'].lower() == songMatch and songDict['result']['primary_artist']['name'].lower() == artistLow:
				mainDict = songDict['result']
				self.perfectmatch = True
				break
			elif songDict['result']['title'].lower() == songLow:
				mainDict = songDict['result']
				break
			
			if len(mainDict)!=0:
				continue
		
		if len(mainDict) == 0:
			try2 = urllib.request.Request(baseURL+songSearch, headers = header)
			try3 = urllib.request.urlopen(try2)
			string2 = try3.read().decode('utf-8')
			jsono2 = json.loads(string2)
			for songDict in jsono2['response']['hits']:
				if songDict['result']['primary_artist']['name'].lower() == artistLow:
					mainDict = songDict["result"]
					break
				
		
		if len(mainDict) == 0:
			lyrics = "Not found"
		
		if len(mainDict) != 0:
			id = mainDict['id']
			url = mainDict['url']
			print(url)
			spoofHead = {'User-Agent' : 'Mozilla/5.0'}
			rex = urllib.request.Request(url, headers = spoofHead)
			rex2 = urllib.request.urlopen(rex)
			f = BeautifulSoup(rex2.read())
		
		'''
		
		Genius has two different ways of nesting lyrics in tags
		the first for loop looks for all things in <p> then <a>
		tags and appends them. Older songs have a few lyrics in
		just the <p> tag, which is what the second loop grabs 
		and stops at the bottom of the lyrics using the text
		Genius Editorial.
		
		'''
		
		if lyrics != "Not found":
			for link in f.find_all('p'):
				for lyric in link.find_all('a'):
					x = lyric.get_text()
					for line in x.splitlines():
						line = line.lower()#.encode('utf-8')
						lyrics1.append(line)
			for link in f.find_all('p'):
				x = link.get_text()
				for lyric in x.splitlines():
					if 'Genius Editorial' not in lyric:
						lyrics2.append(lyric)
					else:
						break
			lyrics = lyrics1
			for line in lyrics2:
				if line not in lyrics:
					lyrics.append(line)
		return(lyrics)

	def checkForSwears(self):
		notPartofOtherWords = ['ass', 'cunt']
		swears = ['pussy','bitch', 'dick', 'fuck', 'shit', 'damn', 'nigga']
		lyrics = self.lyrics
		swearwords = self.swearwords
		hasSwears = 0
		if isinstance(lyrics, list):
			for lyr in lyrics:
				for word in lyr.split():
					if word in notPartofOtherWords:
						hasSwears = 1
						if word not in swearwords:
							swearwords.append(word)
				for swear in swears:
					if swear in lyr:
						hasSwears = 1
						if swear not in swearwords:
							swearwords.append(swear)
			if hasSwears != 0:
				swearBool = True
			else:
				swearBool = False
		elif not isinstance(lyrics, list):
			swearBool = "Unknown - Lyrics not found"
		return(swearBool, swearwords)
		
	def toDict(self):
		indDict = {'Song': self.name,
				'Artist': self.artist,
				'Swears': self.swears,
				'Swear Words': self.swearwords,
				'Perfect Match': self.perfectmatch}
		return indDict

app = Flask(__name__)

@app.route('/')
def main():
	return render_template('index.html')
	
@app.route('/home')
def home():
	return render_template('index.html')
	
@app.route('/spotifyplaylist')
def spotifyplaylist():
	return render_template('spotify.html')

@app.route('/spotifysonglist', methods = ["POST"])
def spotifysonglist():
	finalList, songList = [],[]
	userID = request.form['inputAccount']
	playlistID = request.form['inputPlaylist']
	if not userID:
		return "Please enter an account"
	if not playlistID:
		return "Please enter a playlist"
	"""
	Shamelessly stolen from https://github.com/plamere/spotipy/blob/master/spotipy/oauth2.py
	since I can't install it
	"""
	
	OAUTH_TOKEN_URL = 'https://accounts.spotify.com/api/token'
	client_id = 'cdd615ac771c4c079107b96c34ad8c95'
	client_secret = '254303e522424cf195453f9ca1f575ec'

	payload = { 'grant_type': 'client_credentials'}

	auth_header = base64.b64encode(str(client_id+ ':' + client_secret).encode())
	headers = { 'Authorization': 'Basic %s' % auth_header.decode()}

	response = requests.post(OAUTH_TOKEN_URL, data = payload, headers = headers, verify = True)
	token_info = response.json()
	token = token_info['access_token']
	'''
	/theft
	'''
	header = {'Accept': 'application/json',
	'Authorization': 'Bearer %s' % (token)
	}
	songList = []
	baseurl = 'https://api.spotify.com/v1/users/%s/playlists/%s/tracks' % (userID, playlistID)

	req = urllib.request.Request(baseurl, headers=header)
	req2 = urllib.request.urlopen(req)

	string = req2.read().decode('utf-8')
	jsono = json.loads(string)

	for x in jsono['items']:
		try:
			songList.append(Song(x['track']['name'], x['track']['artists'][0]['name']))
		except:
			pass
	for item in songList:
		if item.swears or not item.perfectmatch:
			format = "! Danger Dog"
		else:
			format = "OK Success Dog"
		indList = [item.name, item.artist, item.swears, item.perfectmatch, format]
		finalList.append(indList)
	return render_template('final.html', result = finalList)



@app.route('/iTunes')
def iTunes():
	return render_template('itunes.html')
	 
@app.route('/songList', methods=["POST"])
def songList():
	finalList, songList = [], []
	file = request.files['data_file']
	if not file:
		return "No file"
	df = pd.read_table(request.files['data_file'])
	tionary = df.to_dict()
	length = range(0,len(tionary["Artist"]))
	for item in length:
		songList.append(Song(tionary['Name'][item], tionary['Artist'][item]))
	for item in songList:
		if item.swears or not item.perfectmatch:
			format = "! Danger Dog"
		else:
			format = "OK Success Dog"
		indList = [item.name, item.artist, item.swears, item.perfectmatch, format]
		finalList.append(indList)
	return render_template('final.html', result = finalList)
	
app.debug = True

	
if __name__ == "__main__":
	app.run()
	

# HelixStudios
import re, os, platform, urllib
from utils import Utils

# import certifi, requests

AGENT_NAME             = 'Helix Studios'
AGENT_VERSION          = '2020.06.27.0'
AGENT_LANGUAGES        = [Locale.Language.NoLanguage, Locale.Language.English]
AGENT_FALLBACK_AGENT   = False
AGENT_PRIMARY_PROVIDER = False
AGENT_CONTRIBUTES_TO   = ['com.plexapp.agents.cockporn']
AGENT_CACHE_TIME       = CACHE_1HOUR * 24

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL = 'https://www.helixstudios.net%s'

# Example Video Details URL
# https://www.helixstudios.net/video/3437/hosing-him-down.html
BASE_VIDEO_DETAILS_URL = BASE_URL % '/video/%s/index.html'

# Example Movie Details URL
# https://www.helixstudios.net/movie/HXM118/index.html
BASE_MOVIE_DETAILS_URL = BASE_URL % '/movie/%s/index.html'

# Example Model Details URL
# https://www.helixstudios.net/model/984/index.html
BASE_MODEL_DETAILS_URL = BASE_URL % '/model/%s/index.html'

# Example Search URL:
# https://www.helixstudios.net/videos/?q=Hosing+Him+Down
BASE_SEARCH_URL = BASE_URL % '/videos/?q=%s'

def Start():
	Log.Info('-----------------------------------------------------------------------')
	Log.Info('[' + AGENT_NAME + '] ' + 'Starting Metadata Agent ' + AGENT_VERSION)
	HTTP.CacheTime = AGENT_CACHE_TIME
	HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; ' \
		'Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; ' \
		'.NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'

def ValidatePrefs():
	Log.Info('[' + AGENT_NAME + '] ' + 'Validating Preferences')
	Log.Debug('[' + AGENT_NAME + '] ' + 'Folder(s) where these items might be found: ' + str(Prefs['folders']))
	Log.Debug('[' + AGENT_NAME + '] ' + 'Regular expression: ' + str(Prefs['regex']))
	Log.Debug('[' + AGENT_NAME + '] ' + 'Cover Images to download: ' + str(Prefs['cover']))
	Log.Debug('[' + AGENT_NAME + '] ' + 'Ouput debugging info in logs: ' + str(Prefs['debug']))
	Log.Info('[' + AGENT_NAME + '] ' + 'Validation Complete')

class HelixStudios(Agent.Movies):
	name = AGENT_NAME
	languages = AGENT_LANGUAGES
	media_types = ['Movie']
	primary_provider = AGENT_PRIMARY_PROVIDER
	fallback_agent = AGENT_FALLBACK_AGENT
	contributes_to = AGENT_CONTRIBUTES_TO

	def log(self, state, message, *args):
		if Prefs['debug']:
			if state == 'info':
				Log.Info('[' + AGENT_NAME + '] ' + ' - ' + message, *args)
			elif state == 'debug':
				Log.Debug('[' + AGENT_NAME + '] ' + ' - ' + message, *args)
			elif state == 'error':
				Log.Error('[' + AGENT_NAME + '] ' + ' - ' + message, *args)

	def noNegative(self, value):
		if(value < 0):
			return 0
		else:
			return value

	def intTest(self, s):
		try:
			int(s)
			return int(s)
		except ValueError:
			return False

	def search(self, results, media, lang, manual):
		self.log('info', '-----------------------------------------------------------------------')
		self.log('debug', 'SEARCH - Platform: %s %s', platform.system(), platform.release())
		self.log('debug', 'SEARCH - media.title - %s', media.title)
		self.log('debug', 'SEARCH - media.items[0].parts[0].file - %s', media.items[0].parts[0].file)
		self.log('debug', 'SEARCH - media.primary_metadata.title - %s', media.primary_metadata.title)
		self.log('debug', 'SEARCH - media.items - %s', media.items)
		self.log('debug', 'SEARCH - media.filename - %s', media.filename)
		self.log('debug', 'SEARCH - lang - %s', lang)
		self.log('debug', 'SEARCH - manual - %s', manual)
		self.log('debug', 'SEARCH - Prefs->cover - %s', Prefs['cover'])
		self.log('debug', 'SEARCH - Prefs->folders - %s', Prefs['folders'])
		self.log('debug', 'SEARCH - Prefs->regex - %s', Prefs['regex'])

		if not media.items[0].parts[0].file:
			return

		path_and_file = media.items[0].parts[0].file.lower()
		self.log('debug', 'SEARCH - File Path: %s', path_and_file)

		enclosing_directory, file_name = os.path.split(os.path.splitext(path_and_file)[0])
		enclosing_directory, enclosing_folder = os.path.split(enclosing_directory)
		self.log('debug', 'SEARCH - Enclosing Folder: %s', enclosing_folder)
		#self.log('debug', 'SEARCH - File Name: %s', file_name)

		if Prefs['folders'] != "*":
			folder_list = re.split(',\s*', Prefs['folders'].lower())
			if enclosing_folder not in folder_list:
				self.log('debug', 'SEARCH - Skipping %s because the folder %s is not in the acceptable folders list: %s', file_name, enclosing_folder, ','.join(folder_list))
				return

		# File names to match for this agent
		self.log('info', 'SEARCH - Regular expression: %s', str(Prefs['regex']))
		try:
			file_name_pattern = re.compile(Prefs['regex'], re.IGNORECASE)
		except Exception as e:
			self.log('error', 'SEARCH - Error regex pattern: %s', e)
			return

		m = file_name_pattern.search(file_name)
		if not m:
			self.log('debug', 'SEARCH - Skipping %s because the file name is not in the expected format.', file_name)
			return

		groups = m.groupdict()
		file_studio = groups['studio']
		self.log('debug', 'SEARCH - Studio: %s', file_studio)

		self.log('debug', 'SEARCH - Skipping %s', AGENT_NAME.lower())
		self.log('debug', 'SEARCH - Skipping %s', file_studio.lower())
		if file_studio is not None and AGENT_NAME.lower() not in file_studio.lower():
			self.log('debug', 'SEARCH - Skipping %s because does not match: %s', file_name, AGENT_NAME)
			return

		clip_name = groups['clip_name']
		movie_url_name = re.sub('\s+', '+', clip_name)

		if "hxm" in clip_name:
			#DVD release, use special indexer
			video_url = BASE_URL % BASE_MOVIE_DETAILS_URL % movie_url_name
			self.log('info', 'SEARCH - DIRECT DVD MATCH: %s', video_url);
			self.rating = 5
			html = HTML.ElementFromURL(video_url, sleep=REQUEST_DELAY)
			video_title = html.xpath('//*[@id="rightcolumn"]/div/div/h3/text()')[0]
			results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
			return

		if clip_name.isdigit():
			#add direct video match & skip search
			video_url = BASE_URL % BASE_VIDEO_DETAILS_URL % movie_url_name
			self.log('info', 'SEARCH - DIRECT SCENE MATCH: %s', video_url);
			self.rating = 5
			html = HTML.ElementFromURL(video_url, sleep=REQUEST_DELAY)
			video_title = html.xpath('//div[@class="scene-title"]/span/text()')[0]
			results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
			return

		movie_url = BASE_SEARCH_URL % movie_url_name
		search_query_raw = list()
		for piece in clip_name.split(' '):
			if re.search('^[0-9A-Za-z]*$', piece.replace('!', '')) is not None:
				search_query_raw.append(piece)

		self.log('debug', 'SEARCH - Video URL: %s', movie_url)
		html = HTML.ElementFromURL(movie_url, sleep=REQUEST_DELAY)

		search_results = html.xpath('//*[@class="video-gallery"]/li')

		score=10
		# Enumerate the search results looking for an exact match. The hope is that by eliminating special character words from the title and searching the remainder that we will get the expected video in the results.
		if search_results:
			for result in search_results:
				video_title = result.find('a').find("img").get("alt")
				video_title = re.sub("[\:\?\|]", '', video_title)
				video_title = re.sub("\s{2,4}", ' ', video_title)
				video_title = video_title.rstrip(' ')

				utils = Utils()
				matchscore = utils.getMatchScore(video_title.lower(), clip_name.lower())
				self.log('debug', 'SEARCH - video title percentage: %s', matchscore)

				self.log('debug', 'SEARCH - video title: %s', video_title)
				if matchscore > 90:
					video_url = result.find('a').get('href')
					self.log('debug', 'SEARCH - video url: %s', video_url)
					self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
					self.log('debug', 'SEARCH - rating: %s', self.rating)
					self.log('debug', 'SEARCH - Exact Match "' + clip_name.lower() + '" == "%s"', video_title.lower())
					results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
					return
				else:
					self.log('debug', 'SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
					score = score-1
					results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))
		else:
			search_query = "+".join(search_query_raw[-2:])
			self.log('debug', 'SEARCH - Search Query: %s', search_query)
			html = HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
			search_results = html.xpath('//*[@class="video-gallery"]/li')
			if search_results:
				for result in search_results:
					video_title = result.find('a').find("img").get("alt")
					video_title = re.sub("[\:\?\|]", '', video_title)
					video_title = video_title.rstrip(' ')
					self.log('debug', 'SEARCH - video title: %s', video_title)
					if video_title.lower() == clip_name.lower():
						video_url = result.find('a').get('href')
						self.log('debug', 'SEARCH - video url: %s', video_url)
						self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
						self.log('debug', 'SEARCH - rating: %s', self.rating)
						self.log('debug', 'SEARCH - Exact Match "' + clip_name.lower() + '" == "%s"', video_title.lower())
						results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
						return
					else:
						self.log('debug', 'SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
						score = score-1
						results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))
			else:
				search_query = "+".join(search_query_raw[:2])
				self.log('debug', 'SEARCH - Search Query: %s', search_query)
				html = HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
				search_results = html.xpath('//*[@class="video-gallery"]/li')
				if search_results:
					for result in search_results:
						video_title = result.find('a').find("img").get("alt")
						video_title = re.sub("[\:\?\|]", '', video_title)
						video_title = video_title.rstrip(' ')
						self.log('debug', 'SEARCH - video title: %s', video_title)
						if video_title.lower() == clip_name.lower():
							video_url = result.find('a').get('href')
							self.log('debug', 'SEARCH - video url: %s', video_url)
							self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
							self.log('debug', 'SEARCH - rating: %s', self.rating)
							self.log('debug', 'SEARCH - Exact Match "' + clip_name.lower() + '" == "%s"', video_title.lower())
							results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
							return
						else:
							self.log('debug', 'SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
							results.Append(MetadataSearchResult(id = '', name = media.filename, score = 1, lang = lang))
				else:
					score = 1
					self.log('debug', 'SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
					return

	def update(self, metadata, media, lang, force=False):
		self.log('info', 'UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.log('info', 'UPDATE - File Path: %s', file_path)
		self.log('info', 'UPDATE - Video URL: %s', metadata.id)
		url = BASE_URL % metadata.id

		# Fetch HTML
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url

		video_title = html.xpath('//div[@class="scene-title"]/span/text()')[0]
		self.log('info', 'UPDATE - video_title: "%s"', video_title)

		# External 	https://cdn.helixstudios.com/img/300h/media/stills/hx109_scene52_001.jpg
		# Member 	https://cdn.helixstudios.com/img/1920w/media/stills/hx109_scene52_001.jpg
		valid_image_names = list()
		valid_art_names = list()
		if "HXM" in url:
			metadata.title = html.xpath('//*[@id="rightcolumn"]/div/div/h3/text()')[0]

			#Movie poster
			mov_cover_lores = html.xpath('//div[@id="rightcolumn"]/a/img')[0].get("src")
			mov_cover_hires = mov_cover_lores.replace("320w","1920w")
			valid_image_names.append(mov_cover_hires)
			metadata.posters[mov_cover_hires]=Proxy.Media(HTTP.Request(mov_cover_hires), sort_order = 1)

			#Background art
			mov_id = str(filter(str.isdigit, url))
			art_url = "https://cdn.helixstudios.com/media/titles/hxm" + mov_id + "_trailer.jpg";
			valid_art_names.append(art_url)
			metadata.art[art_url] = Proxy.Media(HTTP.Request(art_url), sort_order=1)
			metadata.art.validate_keys(valid_art_names)

			#Description
			metadata.summary = html.xpath("//p[@class='description']/text()")[0]

			#Release date
			raw_date = html.xpath('//*[@id="rightcolumn"]/div/div/div[1]/text()')[0]
			metadata.originally_available_at = Datetime.ParseDate(raw_date).date()
			metadata.year = metadata.originally_available_at.year

			#Cast images
			try:
				metadata.roles.clear()
				rolethumbs = list();
				headshot_list = html.xpath('//ul[@id="scene-models"]/li/a/img')
				for headshot_obj in headshot_list:
					headshot_url_lo_res = headshot_obj.get("src")
					headshot_url_hi_res = headshot_url_lo_res.replace("150w","480w")

					result = requests.post('https://neural.vigue.me/facebox/check', json={"url": headshot_url_hi_res}, verify=certifi.where())
					self.log('info', result.json()["facesCount"])
					if result.json()["facesCount"] == 1:
						box = result.json()["faces"][0]["rect"]
						cropped_headshot = "https://cdn.vigue.me/unsafe/" + str(self.noNegative(box["left"] - 100)) + "x" + str(self.noNegative(box["top"] - 100)) + ":" + str(self.noNegative((box["left"]+box["width"])+100)) + "x" + str(self.noNegative((box["top"]+box["height"])+100)) + "/" + headshot_url_hi_res
					else:
						cropped_headshot = headshot_url_hi_res

					rolethumbs.append(cropped_headshot)

				index = 0
				#Cast names
				cast_text_list = html.xpath('//ul[@id="scene-models"]/li/a/div/text()')
				for cast in cast_text_list:
					cname = cast.strip()
					if (len(cname) > 0):
						role = metadata.roles.new()
						role.name = cname
						role.photo = rolethumbs[index]
					index += 1
			except Exception as e:
				self.log('error', 'UPDATE - Error getting cast: %s', e)
		else:
			i = 0
			video_image_list = html.xpath('//*[@id="scene-just-gallery"]/a/img')
			self.log('info', 'UPDATE - video_image_list: "%s"', video_image_list)
			try:
				coverPrefs = Prefs['cover']
				for image in video_image_list:
					if i <= (self.intTest(coverPrefs)-1) or coverPrefs == "all available":
						i = i + 1
						thumb_url = image.get('src')
						poster_url = thumb_url.replace('300h', '1920w')
						valid_image_names.append(poster_url)
						if poster_url not in metadata.posters:
							try:
								metadata.posters[poster_url] = Proxy.Preview(HTTP.Request(thumb_url), sort_order = i)
							except Exception as e:
								pass
			except Exception as e:
				self.log('error', 'UPDATE - Error getting posters: %s', e)

			#Try to get scene background art
			try:
				bg_image = html.xpath('//*[@id="container"]/div[3]/img')[0].get("src")
				valid_art_names.append(bg_image)
				metadata.art[bg_image] = Proxy.Media(HTTP.Request(bg_image), sort_order=1)
				self.log('info', 'UPDATE- Art: %s', bg_image)
			except Exception as e:
				self.log('info', 'UPDATE - Error getting art: %s', e)

			# Try to get description text
			try:
				raw_about_text = html.xpath('//meta[@name="Description"]/@content')
				self.log('info', 'UPDATE - About Text - RAW %s', raw_about_text)
				metadata.summary = raw_about_text[0]
			except Exception as e:
				self.log('error', 'UPDATE - Error getting description text: %s', e)

			# Try to get release date
			try:
				release_date_raw = str(html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr[1]/comment()')[0])
				date_pattern = '(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2}),\s+(\d{4})'
				date_match = re.search(date_pattern, release_date_raw)
				release_date = date_match.group(0)
				self.log('info', 'UPDATE - Release Date - New: %s', release_date)
				metadata.originally_available_at = Datetime.ParseDate(release_date).date()
				metadata.year = metadata.originally_available_at.year
			except Exception as e:
				self.log('error', 'UPDATE - Error getting release date: %s', e)

			# Try to get and process the video cast
			try:
				metadata.roles.clear()
				htmlcast = html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr[1]/td/a')
				self.log('info', 'UPDATE - cast: "%s"', htmlcast)
				for cast in htmlcast:
					if (len(cast.text) > 0):
						role = metadata.roles.new()
						role.name = cast.text

						model_href = BASE_URL % cast.get('href')
						self.log('info', 'UPDATE - cast url: "%s"', model_href)

						try:
							model_page = HTML.ElementFromURL(model_href, sleep=REQUEST_DELAY)
							model_headshot_lo_res = model_page.xpath('//div[@id="modelHeadshot"]/img')[0].get('src')
							headshot_url_hi_res = model_headshot_lo_res.replace("320w","320w")
							#Ask facebox to query image for face bounding boxes
							self.log('info', headshot_url_hi_res);
							try:
								result = requests.post('https://neural.vigue.me/facebox/check', json={"url": headshot_url_hi_res}, verify=certifi.where())
								self.log('info', result.json()["facesCount"])
								if result.json()["facesCount"] == 1:
									box = result.json()["faces"][0]["rect"]
									cropped_headshot = "https://cdn.vigue.me/unsafe/" + str(abs(box["left"] - 50)) + "x" + str(abs(box["top"] - 50)) + ":" + str(abs((box["left"]+box["width"])+50)) + "x" + str(abs((box["top"]+box["height"])+50)) + "/" + headshot_url_hi_res
								else:
									cropped_headshot = headshot_url_hi_res
								#Create new image url from Thumbor CDN with facial bounding box
							except Exception as e:
								self.log('error', 'UPDATE - Error getting video cast image: %s', e)
								self.log('info', 'UPDATE - Trying video cast image backup: %s', headshot_url_hi_res)
								cropped_headshot = headshot_url_hi_res
							self.log("UPDATE - Cropped headshot: %s", cropped_headshot)
							role.photo = cropped_headshot
						except Exception as e:
							self.log('error', 'UPDATE - Error getting video cast image: %s', e)
			except Exception as e:
				self.log('error', 'UPDATE - Error getting video cast: %s', e)

			# Try to get and process the video genres
			try:
				metadata.genres.clear()
				genres = html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr[4]/td/a/text()')
				self.log('info', 'UPDATE - video_genres: "%s"', genres)
				for genre in genres:
					genre = genre.strip()
					if (len(genre) > 0):
						metadata.genres.add(genre)
			except Exception as e:
				self.log('error', 'UPDATE - Error getting video genres: %s', e)
			metadata.rating = float(self.rating)*2
		# End If

		metadata.posters.validate_keys(valid_image_names)
		metadata.art.validate_keys(valid_art_names)
		metadata.collections.add(AGENT_NAME)
		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = AGENT_NAME

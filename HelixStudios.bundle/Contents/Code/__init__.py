# HelixStudios
import re, os, platform, urllib
from utils import Utils

AGENT_NAME             = 'Helix Studios'
AGENT_VERSION          = '2020.06.24.0'
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
BASE_VIDEO_DETAILS_URL = 'https://www.helixstudios.net/video/%s'

# Example Search URL:
# https://www.helixstudios.net/videos/?q=Hosing+Him+Down
BASE_SEARCH_URL = 'https://www.helixstudios.net/videos/?q=%s'

# Example File Name:
# https://media.helixstudios.com/scenes/hx111_scene2/hx111_scene2_member_1080p.mp4
# FILENAME_PATTERN = re.compile("")
# TITLE_PATTERN = re.compile("")

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
	fallback_agent = False
	contributes_to = AGENT_CONTRIBUTES_TO

	def log(self, state, message, *args):
		if Prefs['debug']:
			if state == 'info':
				Log.Info('[' + AGENT_NAME + '] ' + ' - ' + message, *args)
			elif state == 'debug':
				Log.Debug('[' + AGENT_NAME + '] ' + ' - ' + message, *args)
			elif state == 'error':
				Log.Error('[' + AGENT_NAME + '] ' + ' - ' + message, *args)

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
		self.log('info', 'UPDATE - Regular expression: %s', str(Prefs['regex']))
		try:
			file_name_pattern = re.compile(Prefs['regex'], re.IGNORECASE)
		except Exception as e:
			self.log('error', 'UPDATE - Error regex pattern: %s', e)
			return

		m = file_name_pattern.search(file_name)
		if not m:
			self.log('debug', 'SEARCH - Skipping %s because the file name is not in the expected format.', file_name)
			return

		groups = m.groupdict()
		file_studio = groups['studio']
		self.log('debug', 'SEARCH - Studio: %s', file_studio)

		if file_studio is not None and AGENT_NAME.lower() in file_studio.lower():
			self.log('debug', 'SEARCH - Skipping %s because does not match: %s', file_name, AGENT_NAME)
			return

		clip_name = groups['clip_name']
		movie_url_name = re.sub('\s+', '+', clip_name)
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
				# Check the alt tag which includes the full title with special characters against the video title. If we match we nominate the result as the proper metadata. If we don't match we reply with a low score.
				#if video_title.lower() == clip_name.lower():
				if matchscore > 90:
					video_url=result.find('a').get('href')
					self.log('debug', 'SEARCH - video url: %s', video_url)
					self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
					self.log('debug', 'SEARCH - rating: %s', self.rating)
					self.log('debug', 'SEARCH - Exact Match "' + clip_name.lower() + '" == "%s"', video_title.lower())
					results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
					return
				else:
					self.log('debug', 'SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
					score=score-1
					results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))
		else:
			search_query="+".join(search_query_raw[-2:])
			self.log('debug', 'SEARCH - Search Query: %s', search_query)
			html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
			search_results=html.xpath('//*[@class="video-gallery"]/li')
			if search_results:
				for result in search_results:
					video_title = result.find('a').find("img").get("alt")
					video_title = re.sub("[\:\?\|]", '', video_title)
					video_title = video_title.rstrip(' ')
					self.log('debug', 'SEARCH - video title: %s', video_title)
					if video_title.lower() == clip_name.lower():
						video_url=result.find('a').get('href')
						self.log('debug', 'SEARCH - video url: %s', video_url)
						self.rating = result.find('.//*[@class="current-rating"]').text.strip('Currently ').strip('/5 Stars')
						self.log('debug', 'SEARCH - rating: %s', self.rating)
						self.log('debug', 'SEARCH - Exact Match "' + clip_name.lower() + '" == "%s"', video_title.lower())
						results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
						return
					else:
						self.log('debug', 'SEARCH - Title not found "' + clip_name.lower() + '" != "%s"', video_title.lower())
						score=score-1
						results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))
			else:
				search_query="+".join(search_query_raw[:2])
				self.log('debug', 'SEARCH - Search Query: %s', search_query)
				html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
				search_results=html.xpath('//*[@class="video-gallery"]/li')
				if search_results:
					for result in search_results:
						video_title=result.find('a').find("img").get("alt")
						video_title = re.sub("[\:\?\|]", '', video_title)
						video_title = video_title.rstrip(' ')
						self.log('debug', 'SEARCH - video title: %s', video_title)
						if video_title.lower() == clip_name.lower():
							video_url=result.find('a').get('href')
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
					score=1
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
		# Member 	https://cdn.helixstudios.com/img/250w/media/stills/hx109_scene52_001.jpg
		valid_image_names = list()
		i = 0
		video_image_list = html.xpath('//*[@id="scene-just-gallery"]/a/img')
		# self.log('info', 'UPDATE - video_image_list: "%s"', video_image_list)
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
							metadata.posters[poster_url]=Proxy.Preview(HTTP.Request(thumb_url), sort_order = i)
						except: pass
		except Exception as e:
			self.log('error', 'UPDATE - Error getting posters: %s', e)
			pass

		# Try to get description text
		try:
			raw_about_text = html.xpath('//meta[@name="Description"]/@content')
			self.log('info', 'UPDATE - About Text - RAW %s', raw_about_text)
			metadata.summary = raw_about_text[0]
		except Exception as e:
			self.log('error', 'UPDATE - Error getting description text: %s', e)
			pass

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
			pass

		# Try to get and process the video cast
		try:
			metadata.roles.clear()
			htmlcast = html.xpath('//*[@id="main"]/div[1]/div[1]/div[2]/table/tr[1]/td/a/text()')
			self.log('info', 'UPDATE - cast: "%s"', htmlcast)
			for cast in htmlcast:
				cname = cast.strip()
				if (len(cname) > 0):
					role = metadata.roles.new()
					role.name = cname
		except Exception as e:
			self.log('error', 'UPDATE - Error getting video cast: %s', e)
			pass

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
			pass

		metadata.posters.validate_keys(valid_image_names)
		metadata.rating = float(self.rating)*2

		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = AGENT_NAME

# Staxus
import re, os, platform, urllib, cgi
#-*- coding: utf-8 -*-

AGENT_NAME             = 'Staxus'
AGENT_VERSION          = '2020.06.21.0'
AGENT_LANGUAGES        = [Locale.Language.NoLanguage, Locale.Language.English]
AGENT_FALLBACK_AGENT   = False
AGENT_PRIMARY_PROVIDER = False
AGENT_CONTRIBUTES_TO   = ['com.plexapp.agents.cockporn']
AGENT_CACHE_TIME       = CACHE_1HOUR * 24

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL='http://staxus.com%s'

# Example Video Details URL
# http://staxus.com/trial/gallery.php?id=4044
BASE_VIDEO_DETAILS_URL='http://staxus.com/trial/%s'

# Example Search URL:
# http://staxus.com/trial/search.php?query=Staxus+Classic%3A+BB+Skate+Rave+-+Scene+1+-+Remastered+in+HD
BASE_SEARCH_URL='http://staxus.com/trial/search.php?st=advanced&qall=%s'

# File names to match for this agent
file_name_pattern = re.compile(Prefs['regex'])

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

class Staxus(Agent.Movies):
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
		self.log('debug', 'SEARCH - File Name: %s', file_name)

		if Prefs['folders'] != "*":
			folder_list = re.split(',\s*', Prefs['folders'].lower())
			if enclosing_folder not in folder_list:
				self.log('debug', 'SEARCH - Skipping %s because the folder %s is not in the acceptable folders list: %s', file_name, enclosing_folder, ','.join(folder_list))
				return

		m = file_name_pattern.search(file_name)
		if not m:
			self.log('debug', 'SEARCH - Skipping %s because the file name is not in the expected format.', file_name)
			return

		groups = m.groupdict()
		file_studio = groups['studio']
		self.log('debug', 'SEARCH - Studio: %s', file_studio)

		if file_studio is not None and file_studio.lower() != AGENT_NAME.lower():
			self.log('debug', 'SEARCH - Skipping %s because does not match: %s', file_name, AGENT_NAME)
			return

		clip_name = groups['clip_name']
		self.log('debug', 'SEARCH - Split File Name: %s', file_name.split(' '))

		remove_words = file_name.lower()
		remove_words = remove_words.replace(AGENT_NAME.lower(), '')
		remove_words = re.sub('\(([^\)]+)\)', '', remove_words) #Removes anything inside of () and the () themselves.
		remove_words = remove_words.strip(' ')
		search_query_raw = list()
		# Process the split filename to remove words with special characters. This is to attempt to find a match with the limited search function(doesn't process any non-alphanumeric characters correctly)
		for piece in remove_words.split(' '):
			search_query_raw.append(cgi.escape(piece))
		search_query = "%2C+".join(search_query_raw)
		self.log('debug', 'SEARCH - Search Query: %s', search_query)
		html = HTML.ElementFromURL(BASE_SEARCH_URL % search_query.replace('–', '-'), sleep=REQUEST_DELAY)
		search_results = html.xpath('//*[@class="item"]')
		score = 10
		self.log('debug', 'SEARCH - results size: %s', len(search_results))
		# Enumerate the search results looking for an exact match. The hope is that by eliminating special character words from the title and searching the remainder that we will get the expected video in the results.
		for result in search_results:
			#result=result.find('')
			video_title=result.findall("div/a/img")[0].get("alt")
			video_title = video_title.lstrip(' ') #Removes white spaces on the left end.
			video_title = video_title.rstrip(' ') #Removes white spaces on the right end.
			self.log('debug', 'SEARCH - video title: %s', video_title)
			# Check the alt tag which includes the full title with special characters against the video title. If we match we nominate the result as the proper metadata. If we don't match we reply with a low score.
			if video_title.lower().replace(':','') == file_name.lower():
				video_url=result.findall("div/a")[0].get('href')
				self.log('debug', 'SEARCH - video url: %s', video_url)
				image_url=result.findall("div/a/img")[0].get("src")
				self.log('debug', 'SEARCH - image url: %s', image_url)
				self.log('debug', 'SEARCH - Exact Match "' + file_name.lower() + '" == "%s"' % video_title.lower())
				results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 100, lang = lang))
			else:
				self.log('debug', 'SEARCH - Title not found "' + file_name.lower() + '" != "%s"' % video_title.lower())
				score=score-1
				results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))

	def update(self, metadata, media, lang, force=False):
		self.log('info', 'UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.log('info', 'UPDATE - File Path: %s', file_path)
		self.log('info', 'UPDATE - Video URL: %s', metadata.id)
		url = BASE_VIDEO_DETAILS_URL % metadata.id

		# Fetch HTML
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url

		video_title = html.xpath('//div[@class="video-descr__title"]//h2/text()')[0]
		self.log('info', 'UPDATE - video_title: "%s"' % video_title)

		video_image_list = html.xpath('//div[contains(@class, "gallery-image")]/a/@style')
		self.log('info', 'UPDATE - video_image_list: "%s"' % video_image_list)
		try:
			valid_image_names = list()
			video_image_pattern = "'([^' ]+)'"
			i = 0
			coverPrefs = Prefs['cover']
			for image in video_image_list:
				if i != coverPrefs or coverPrefs == "all available":
					thumb_url = re.search(video_image_pattern, image).group(1)
					thumb_url = thumb_url.replace('//', 'https://')
					self.log('info', 'UPDATE - thumb_url: "%s"' % thumb_url)
					# poster_url = thumb_url.replace('300h', '1920w')
					# self.log('info', 'UPDATE - poster_url: "%s"' % poster_url)
					valid_image_names.append(thumb_url)
					if thumb_url not in metadata.posters:
						try:
							i += 1
							metadata.posters[thumb_url]=Proxy.Preview(HTTP.Request(thumb_url), sort_order = i)
						except: pass
		except Exception as e:
			self.log('info', 'UPDATE - Error getting posters: %s', e)
			pass

		# Try to get description text.
		try:
			raw_about_text = html.xpath('//div[@class="video-descr__content"]/p')
			about_text = ' '.join(str(x.text_content().strip()) for x in raw_about_text)
			self.log('info', 'UPDATE - About Text: %s', about_text)
			metadata.summary = about_text
		except Exception as e:
			self.log('info', 'UPDATE - Error getting description text: %s', e)
			pass

		# Try to get release date.
		try:
			release_date_raw = str(html.xpath('//*/text()'))
			date_pattern = '(\d{1,2})\/(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\/+(\d{4})'
			date_match = re.search(date_pattern, release_date_raw).group(0)
			release_date = Datetime.ParseDate(date_match).date()
			self.log('info', 'UPDATE - Release Date: %s', release_date)
			metadata.originally_available_at = release_date
			metadata.year = metadata.originally_available_at.year
		except Exception as e:
			self.log('info', 'UPDATE - Error getting release date: %s', e)
			pass

		# Try to get and process the video cast.
		try:
			metadata.roles.clear()
			htmlcast = html.xpath('//div[@class="video-descr__model-listing"]/div/p/a/text()')
			self.log('info', 'UPDATE - cast: "%s"' % htmlcast)
			for cast in htmlcast:
				cname = cast.strip()
				if (len(cname) > 0):
					role = metadata.roles.new()
					role.name = cname
		except Exception as e:
			self.log('info', 'UPDATE - Error getting video cast: %s', e)
			pass

		# Try to get and process the video genres.
		try:
			metadata.genres.clear()
			genres = html.xpath('//div[@class="video-descr__section"]/p/a/text()')
			self.log('info', 'UPDATE - video_genres: "%s"' % genres)
			for genre in genres:
				genre = genre.strip()
				if (len(genre) > 0):
					metadata.genres.add(genre)
		except Exception as e:
			self.log('info', 'UPDATE - Error getting video genres: %s', e)
			pass

		# Try to get and process the ratings.
		rating = html.xpath('//span[@class="video-grade-average"]/strong/text()')[0]
		self.log('info', 'UPDATE - video_rating: "%s"', rating)
		rating_count_raw = html.xpath('//span[@class="video-grade-total"]/text()')[0]
		self.log('info', 'UPDATE - rating_count_raw: "%s"', rating_count_raw)
		count_pattern = '\d+'
		rating_count = re.search(count_pattern, rating_count_raw).group(0)
		self.log('info', 'UPDATE - video_rating_count: "%s"', rating_count)
		try:
			metadata.rating = float(rating)*2
			metadata.rating_count = int(rating_count)
		except Exception as e:
			self.log('info', 'UPDATE - Error getting rating: %s', e)
			pass

		metadata.posters.validate_keys(valid_image_names)

		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = AGENT_NAME

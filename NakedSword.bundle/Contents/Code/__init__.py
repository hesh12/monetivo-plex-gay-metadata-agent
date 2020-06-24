# NakedSword
import re, os, platform, urllib, cgi

AGENT_NAME             = 'NakedSword'
AGENT_VERSION          = '2020.06.23.0'
AGENT_LANGUAGES        = [Locale.Language.NoLanguage, Locale.Language.English]
AGENT_FALLBACK_AGENT   = False
AGENT_PRIMARY_PROVIDER = False
AGENT_CONTRIBUTES_TO   = ['com.plexapp.agents.cockporn']
AGENT_CACHE_TIME       = CACHE_1HOUR * 24

# Delay used when requesting HTML, may be good to have to prevent being
# banned from the site
REQUEST_DELAY = 0

# URLS
BASE_URL='http://www.nakedsword.com'
BASE_VIDEO_DETAILS_URL=BASE_URL + 'movies/%s'
BASE_SEARCH_URL='http://www.nakedsword.com/scenes/for/text/%s?content=Movies'

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

class NakedSword(Agent.Movies):
	name = AGENT_NAME
	languages = AGENT_LANGUAGES
	media_types = ['Movie']
	primary_provider = AGENT_PRIMARY_PROVIDER
	fallback_agent = False
	contributes_to = AGENT_CONTRIBUTES_TO

	def log(self, state, message, *args):
		if Prefs['debug']:
			if state == 'info':
				Log.Info('[' + AGENT_NAME + '] ' +  ' - ' + message, *args)
			elif state == 'debug':
				Log.Debug('[' + AGENT_NAME + '] ' +  ' - ' + message, *args)

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

		path_and_file = os.path.splitext(path_and_file)[0]
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

		search_query_raw = list()
		file_studio = groups['studio']
		self.log('debug', 'SEARCH - Studio: %s', file_studio)

		if file_studio is not None and file_studio.lower() != AGENT_NAME.lower():
			self.log('debug', 'SEARCH - Skipping %s because does not match: %s', file_name, AGENT_NAME)
			return

		if groups['clip_name'].find("scene") > 0:
			self.log('debug', 'SEARCH - This is a scene: True')
			scene = groups['clip_name'].split("scene", 1)[1].strip()
			file_name = file_name.split("scene", 1)[0].strip()
			self.log('debug', 'SEARCH - Movie: %s', file_name)
			self.log('debug', 'SEARCH - Scene: %s', scene)
			for piece in file_name.split(' '):
				search_query_raw.append(cgi.escape(piece))
		else:
			self.log('debug', 'SEARCH - This is a scene: False')
			file_name = groups['clip_name']
			self.log('info', 'DEBUG - file_name: %s', file_name)
			file_name = file_name.lstrip('- ')
			file_name = file_name.strip()
			self.log('debug', 'SEARCH - Split File Name: %s', file_name.split(' '))
			for piece in file_name.split(' '):
				search_query_raw.append(cgi.escape(piece))

		stopwords = ['for', 'my', 'it', 'ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such', 'into', 'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who', 'as', 'from', 'him', 'each', 'the', 'themselves', 'until', 'below', 'are', 'we', 'these', 'your', 'his', 'through', 'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this', 'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had', 'she', 'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and', 'been', 'have', 'in', 'will', 'on', 'does', 'yourselves', 'then', 'that', 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too', 'only', 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't', 'being', 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing', 'it', 'how', 'further', 'was', 'here', 'than']
		for word in list(search_query_raw):  # iterating on a copy since removing will mess things up
			if word in stopwords:
				search_query_raw.remove(word)
		search_query="+".join(search_query_raw)
		self.log('debug', 'SEARCH - Search Query: %s', search_query)

		html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
		score=10
		search_results=html.xpath('//div[contains(@class, "BoxResultsMainCol")]')

		# Enumerate the search results looking for an exact match. The hope is that by eliminating special character words from the title and searching the remainder that we will get the expected video in the results.
		self.log('debug', 'SEARCH - results size: %s', len(search_results))
		for result in search_results:
			#result=result.find('')
			video_title=result.findtext("div/div[2]/div/div/a")
			self.log('debug', 'SEARCH - video title: %s', video_title)
			# Check the alt tag which includes the full title with special characters against the video title. If we match we nominate the result as the proper metadata. If we don't match we reply with a low score.
			if video_title.lower() == file_name.lower():
				video_url = result.findall("div/div[2]/div/div/a")[0].get('href')
				if BASE_URL not in video_url:
					video_url = BASE_URL + video_url
				self.log('debug', 'SEARCH - video url: %s', video_url)
				image_url = result.findall("div/div[1]/div/a/img")[0].get("src")
				image_url = BASE_URL + image_url
				self.log('debug', 'SEARCH - image url: %s', image_url)
				self.log('debug', 'SEARCH - Exact Match "' + file_name.lower() + '" == "%s"' % video_title.lower())
				results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 98, lang = lang))
				return
			else:
				self.log('debug', 'SEARCH - Title not found "' + file_name.lower() + '" != "%s"' % video_title.lower())
				score=score-1
				results.Append(MetadataSearchResult(id = '', name = media.filename, score = score, lang = lang))

	def update(self, metadata, media, lang, force=False):
		self.log('info', 'UPDATE CALLED')

		enclosing_directory, file_name = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
		file_name = file_name.lower()

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.log('info', 'UPDATE - File Path: %s', file_path)
		self.log('info', 'UPDATE - Video URL: %s', metadata.id)
		url = metadata.id

		# Fetch HTML.
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL.
		metadata.tagline = url
		# Set video title.
		def title(self, html, file_name):
			video_title = [0, 1]
			if file_name.find("scene") > 0:
				video_titles = html.xpath('//div[@class="movieDetailsSceneResults"]/div/div[1]/div[@class="title"]/text()')
				if video_titles > 0:
					i = 0
					for temp in video_titles:
						video_titles[i] = temp.rstrip().replace(":","")
						i += 1

					video_titles = filter(None, video_titles)
					self.log('info', 'UPDATE - Number of Scenes: "%s"' % len(video_titles))
					i = 0
					for temp in video_titles:
						i += 1
						if temp.lower() == file_name.lower():
							video_title[0] = temp
							video_title[1] = i
							self.log('info', 'UPDATE - Scene found in list: "%s"' %temp.lower() + ' == "%s"' %file_name.lower())
							return video_title;
						else:
							video_title[0] = html.xpath('//div[@class="componentHeader"]/h1/text()')[0]
							self.log('info', 'UPDATE - Scene not found in list: "%s"' %temp.lower() + ' != "%s"' %file_name.lower())
				else:
					video_title[0] = html.xpath('//div[@class="MiMovieTitle"]/text()')[0]
					self.log('info', 'UPDATE - Scene not found in list')
			else:
				video_title[0] = html.xpath('//div[@class="MiMovieTitle"]/text()')[0]
			return video_title;
		video_title = title(self, html, file_name)
		self.log('info', 'UPDATE - video_title: "%s"' % video_title[0])

		# Try to get and process the director posters.
		valid_image_names = list()
		i = 0
		image = html.xpath('//div[@class="BoxCoverRollover"]/a/img')[0]
		try:
			poster_url = image.get('src')
			thumb_url = poster_url.replace('xlf', '160w')

			self.log('info', 'UPDATE - thumb_url: "%s"' % thumb_url)
			self.log('info', 'UPDATE - poster_url: "%s"' % poster_url)
			valid_image_names.append(poster_url)
			if poster_url not in metadata.posters:
				try:
					i += 1
					metadata.posters[poster_url]=Proxy.Preview(HTTP.Request(thumb_url), sort_order = i)
				except: pass
		except: pass
		# Try to get description text.
		try:
			raw_about_text=html.xpath('//div[@class="MIDescriptHolder"]')
			self.log('info', 'UPDATE - About Text - RAW %s', raw_about_text)
			about_text=' '.join(str(x.text_content().strip()) for x in raw_about_text)
			metadata.summary=about_text
		except Exception as e:
			self.log('info', 'UPDATE - Error getting description text: %s', e)
			pass

		# Try to get and process the release date.
		#try:
		#	rd=html.xpath('//span[@itemprop="datePublished"]/text()')[0]
		#	self.log('info', 'UPDATE - Release Date: %s', rd)
		#	metadata.originally_available_at = Datetime.ParseDate(rd).date()
		#	metadata.year = metadata.originally_available_at.year
		#except Exception as e:
		#	self.log('info', 'UPDATE - Error getting release date: %s', e)
		#	pass

		# Try to get and process the video genres.
		try:
			metadata.genres.clear()
			if file_name.find("scene") > 0 and file_name.lower() == video_title[0].lower():
				path = '//div[@class="movieDetailsSceneResults"]/div['+str(video_title[1])+']/div[2]/div[5]/div/div/div[2]/span[2]/a/text()'
				genres = html.xpath(path)
				self.log('info', 'UPDATE - video_genres count from scene: "%s"' % len(genres))
				self.log('info', 'UPDATE - video_genres from scene: "%s"' % genres)
				for genre in genres:
					genre = genre.strip()
					if (len(genre) > 0):
						metadata.genres.add(genre)
			else:
				genres = html.xpath('//a[@class="MITheme"]/text()')
				self.log('info', 'UPDATE - video_genres count from movie: "%s"' % len(genres))
				self.log('info', 'UPDATE - video_genres from movie: "%s"' % genres)
				for genre in genres:
					genre = genre.strip()
					if (len(genre) > 0):
						metadata.genres.add(genre)
		except Exception as e:
			self.log('info', 'UPDATE - Error getting video genres: %s', e)
			pass

		# Crew.
		# Try to get and process the director.
		try:
			metadata.directors.clear()
			director = html.xpath('//a[@class="MIDirector"]/text()')[0]
			self.log('info', 'UPDATE - director: "%s"', director)
			metadata.directors.add(director)
		except Exception as e:
			self.log('info', 'UPDATE - Error getting director: %s', e)
			pass

		# Try to get and process the video cast.
		try:
			metadata.roles.clear()
			if file_name.find("scene") > 0 and file_name.lower() == video_title[0].lower():
				path = '//div[@class="movieDetailsSceneResults"]/div['+str(video_title[1])+']/div[2]/div[5]/div/div/div[1]/span[2]/a/span/text()'
				htmlcast = html.xpath(path)
				self.log('info', 'UPDATE - cast scene count: "%s"' % len(htmlcast))
				if len(htmlcast) > 0:
					self.log('info', 'UPDATE - cast: "%s"' % htmlcast)
					for cast in htmlcast:
						cname = cast.strip()
						if (len(cname) > 0):
							role = metadata.roles.new()
							role.name = cname
				else:
					htmlcast = html.xpath('//div[@class="md-detailsStars"]/div/div[1]/a/span/text()')
					htmlcast1 = html.xpath('//div[@class="md-detailsStars"]/div/div[2]/a/span/text()')
					if len(htmlcast1) > 0:
						self.log('info', 'UPDATE - cast: "%s"' % htmlcast1)
						for cast in htmlcast1:
							cname = cast.strip()
							if (len(cname) > 0):
								role = metadata.roles.new()
								role.name = cname
					else:
						self.log('info', 'UPDATE - cast: "%s"' % htmlcast)
						for cast in htmlcast:
							cname = cast.strip()
							if (len(cname) > 0):
								role = metadata.roles.new()
								role.name = cname
			else:
				htmlcast = html.xpath('//a[@class="MIStar"]/text()')
				self.log('info', 'UPDATE - cast: "%s"' % htmlcast)
				for cast in htmlcast:
					cname = cast.strip()
					if (len(cname) > 0):
						role = metadata.roles.new()
						role.name = cname
		except Exception as e:
			self.log('info', 'UPDATE - Error getting cast: %s', e)
			pass

		# Try to get and process the studio name.
		try:
			studio = html.xpath('//a[@class="MIStudio"]/text()')[0]
			self.log('info', 'UPDATE - studio: "%s"', studio)
			metadata.studio=studio
		except Exception as e:
			self.log('info', 'UPDATE - Error getting studio name: %s', e)
			pass

		metadata.content_rating = 'X'
		metadata.posters.validate_keys(valid_image_names)
		metadata.title = video_title[0]

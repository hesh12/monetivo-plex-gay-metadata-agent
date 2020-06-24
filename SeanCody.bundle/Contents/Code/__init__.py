# SeanCody
import re, os, platform, simplejson as json

AGENT_NAME             = 'Sean Cody'
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
BASE_URL = 'https://www.seancody.com%s'

# Example Tour URL
# http://www.seancody.com/tour/movie/9291/brodie-cole-bareback/trailer/
BASE_TOUR_MOVIE_URL = 'http://www.seancody.com/tour/movie/%s/%s/trailer'

# File names to match for this agent
movie_pattern = re.compile(Prefs['regex'])

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

class SeanCody(Agent.Movies):
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

		enclosing_directory, file_name = os.path.split(os.path.splitext(path_and_file)[0])
		enclosing_directory, enclosing_folder = os.path.split(enclosing_directory)
		self.log('debug', 'SEARCH - Enclosing Folder: %s', enclosing_folder)
		self.log('debug', 'SEARCH - File Name: %s', file_name)

		if Prefs['folders'] != "*":
			folder_list = re.split(',\s*', Prefs['folders'].lower())
			if enclosing_folder not in folder_list:
				self.log('debug', 'SEARCH - Skipping %s because the folder %s is not in the acceptable folders list: %s', file_name, enclosing_folder, ','.join(folder_list))
				return

		m = movie_pattern.search(file_name)
		if not m:
			self.log('debug', 'SEARCH - Skipping %s because the file name is not in the expected format.', file_name)
			return

		self.log('debug', 'SEARCH - File Name: %s' % file_name)
		self.log('debug', 'SEARCH - Split File Name: %s' % file_name.split(' '))

		groups = m.groupdict()
		file_studio = groups['studio']
		self.log('debug', 'SEARCH - Studio: %s', file_studio)

		if file_studio is not None and file_studio.lower() != AGENT_NAME.lower():
			self.log('debug', 'SEARCH - Skipping %s because does not match: %s', file_name, AGENT_NAME)
			return

		movie_url_name = re.sub('[^a-z0-9\-]', '', re.sub(' +', '-', groups['clip_name']))
		movie_url = BASE_TOUR_MOVIE_URL + groups['clip_number'] + movie_url_name

		self.log('debug', 'SEARCH - Video URL: %s' % movie_url)
		try:
			html = HTML.ElementFromURL(movie_url, sleep=REQUEST_DELAY)
		except:
			self.log('info', "SEARCH - Title not found: %s" % movie_url)
			return

		movie_name = html.xpath('//*[@id="player-wrapper"]/div/h1/text()')[0]
		self.log('debug', 'SEARCH - title: %s' % movie_name)
		results.Append(MetadataSearchResult(id=movie_url, name=movie_name, score=100, lang=lang))
		return

	def fetch_summary(self, html, metadata):
		raw_about_text = html.xpath('//*[@id="description"]/p')
		self.log('info', 'UPDATE - About Text - RAW %s', raw_about_text)
		about_text = ' '.join(str(x.text_content().strip()) for x in raw_about_text)
		metadata.summary = about_text

	def fetch_release_date(self, html, metadata):
		release_date = html.xpath('//*[@id="player-wrapper"]/div/span/time/text()')[0].strip()
		self.log('info', 'UPDATE - Release Date - New: %s' % release_date)
		metadata.originally_available_at = Datetime.ParseDate(release_date).date()
		metadata.year = metadata.originally_available_at.year

	def fetch_roles(self, html, metadata):
		metadata.roles.clear()
		htmlcast = html.xpath('//*[@id="scroll"]/div[2]/ul[2]/li/a/span/text()')
		self.log('info', 'UPDATE - cast: "%s"' % htmlcast)
		for cast in htmlcast:
			cname = cast.strip()
			if (len(cname) > 0):
				role = metadata.roles.new()
				role.name = cname

	def fetch_genre(self, html, metadata):
		metadata.genres.clear()
		genres = html.xpath('//*[@id="scroll"]/div[2]/ul[1]/li/a/text()')
		self.log('info', 'UPDATE - video_genres: "%s"' % genres)
		for genre in genres:
			genre = genre.strip()
			if (len(genre) > 0):
				metadata.genres.add(genre)

	def fetch_gallery(self, html, metadata):
		i = 0

		# convert the gallery source variable to parseable JSON and then
		# grab the useful bits out of it
		gallery_info = json.loads(html.xpath('/html/body/div[1]/div/div/section[2]/div/script/text()')[0].
			replace('\n', '').
			replace('var gallerySource = ', '').
			replace('};', '}'))

		try:
			coverPrefs = int(Prefs['cover'])
		except ValueError:
			# an absurdly high number means "download all the things"
			coverPrefs = 10000

		thumb_path = gallery_info['thumb']['path']
		thumb_hash = gallery_info['thumb']['hash']
		poster_path = gallery_info['fullsize']['path']
		poster_hash = gallery_info['fullsize']['hash']
		gallery_length = int(gallery_info['length'])
		valid_image_names = []

		for i in xrange(1, gallery_length + 1):
			if i > coverPrefs:
				break

			thumb_url = "%s%02d.jpg%s" % (thumb_path, i, thumb_hash)
			poster_url = "%s%02d.jpg%s" % (poster_path, i, poster_hash)

			valid_image_names.append(poster_url)
			if poster_url not in metadata.posters:
				try:
					i += 1
					metadata.posters[poster_url] = Proxy.Preview(HTTP.Request(thumb_url), sort_order=i)
				except:
					pass

		return valid_image_names

	def update(self, metadata, media, lang, force=False):
		self.log('info', 'UPDATE CALLED')

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.log('info', 'UPDATE - File Path: %s', file_path)
		self.log('info', 'UPDATE - Video URL: %s', metadata.id)

		# Fetch HTML
		html = HTML.ElementFromURL(metadata.id, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = metadata.id

		# The Title
		video_title = html.xpath('//*[@id="player-wrapper"]/div/h1/text()')[0]

		# Try to get description text
		try:
			self.fetch_summary(html, metadata)
		except:
			pass

		# Try to get release date
		try:
			self.fetch_release_date(html, metadata)
		except:
			pass

		# Try to get and process the video cast
		try:
			self.fetch_roles(html, metadata)
		except:
			pass

		# Try to get and process the video genres
		try:
			self.fetch_genres(html, metadata)
		except:
			pass

		valid_image_names = self.fetch_gallery(html, metadata)
		metadata.posters.validate_keys(valid_image_names)

		metadata.content_rating = 'X'
		metadata.title = video_title
		metadata.studio = AGENT_NAME

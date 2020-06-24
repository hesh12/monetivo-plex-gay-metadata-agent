# FraternityX
import re, os, platform, urllib, cgi

AGENT_NAME             = 'FraternityX'
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
BASE_URL='https://fraternityx.com/episode/%s'
BASE_SEARCH_URL='https://www.google.com/search?q=site%%3Afraternityx.com+%s'

def Start():
	Log.Info('-----------------------------------------------------------------------')
	Log.Info('[' + AGENT_NAME + '] ' + 'Starting Metadata Agent ' + AGENT_VERSION)
	HTTP.CacheTime = 0
	HTTP.Headers['Cookie'] = 'pp-accepted=true' #Bypasses the age verification screen
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

class FraternityX(Agent.Movies):
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

	def search(self, results, media, lang):
		self.log('info', '-----------------------------------------------------------------------')
		self.log('debug', 'SEARCH - Platform: %s %s', platform.system(), platform.release())
		self.log('debug', 'SEARCH - results - %s', results)
		self.log('debug', 'SEARCH - media.title - %s', media.title)
		self.log('debug', 'SEARCH - media.items[0].parts[0].file - %s', media.items[0].parts[0].file)
		self.log('debug', 'SEARCH - media.filename - %s', media.filename)
		self.log('debug', 'SEARCH - %s', results)

		if not media.items[0].parts[0].file:
			return

		path_and_file = media.items[0].parts[0].file
		self.log('debug', 'SEARCH - File Path: %s', path_and_file)

		path_and_file = os.path.splitext(path_and_file)[0]
		enclosing_directory, file_name = os.path.split(os.path.splitext(path_and_file)[0])
		enclosing_directory, enclosing_folder = os.path.split(enclosing_directory)
		self.log('debug', 'SEARCH - Enclosing Folder: %s', enclosing_folder)
		self.log('debug', 'SEARCH - File Name: %s', file_name)

		if Prefs['folders'] != "*":
			folder_list = re.split(',\s*', Prefs['folders'])
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

		if file_studio is not None and file_studio.lower() != AGENT_NAME.lower():
			self.log('debug', 'SEARCH - Skipping %s because does not match: %s', file_name, AGENT_NAME)
			return

		clean_file_name = re.sub('[^A-Za-z0-9]+', ' ', file_name)
		self.log('debug', 'SEARCH - Clean title: %s', clean_file_name)

		search_query_raw = list()
		clip_name = groups['clip_name']
		self.log('debug', 'SEARCH - Clip name: %s', clip_name)
		for piece in clip_name.split(' '):
			search_query_raw.append(cgi.escape(piece))

		search_query="+".join(search_query_raw)
		search_query=str.lower(search_query)
		self.log('debug', 'SEARCH - Search Query: %s', search_query)
		html=HTML.ElementFromURL(BASE_SEARCH_URL % search_query, sleep=REQUEST_DELAY)
		score=10
		search_results=html.xpath('//*[@class="srg"]/*[@class="g"][1]')
		self.log('debug', 'SEARCH - Results: %s', len(search_results))

		if len(search_results) > 0:
			self.log('debug', 'SEARCH - results size exact match: %s', len(search_results))
			for result in search_results:
				video_title = result.xpath('//*[@class="srg"]/*[@class="g"]//h3/text()')[0]
				video_url = result.xpath('//*[@class="srg"]/*[@class="g"]//a/@href')[0]
				self.log('debug', 'SEARCH - Exact video title: %s', video_title)
				self.log('debug', 'SEARCH - Exact video URL: %s', video_url)
				results.Append(MetadataSearchResult(id = video_url, name = video_title, score = 98, lang = lang))
				return
		else:
			self.log('debug', 'SEARCH - Results size: %s', len(search_results))
			for result in search_results:
				video_title = result.findall('//*[@class="srg"]/*[@class="g"]//h3/text()')
				video_title = video_title.strip()
				video_title = video_title.replace(':', '')
				self.log('debug', 'SEARCH - Video title: %s', video_title)
			return

	def fetch_title(self, html, metadata):
		self.log('info', 'UPDATE: fetch_title CALLED')
		try:
			video_title=html.xpath('//*[@class="episode-description"]/h1/text()')[0]
			self.log('info', 'UPDATE - Summary: %s', video_title)
			metadata.title = video_title
		except Exception as e:
			self.log('error', 'UPDATE - Error getting title text: %s', e)
			pass

	def fetch_date(self, html, metadata):
		self.log('info', 'UPDATE: fetch_date CALLED')
		try:
			release_date = html.xpath('substring-before(//*[@class="episode-description"]/p/text(), " - ")')
			self.log('info', 'UPDATE - Release Date: %s' % release_date)
			#date_original = datetime.datetime.strptime(release_date, '%Y-%m-%d').strftime('%b %-d, %Y')
			date_original = Datetime.ParseDate(release_date).date()
			self.log('info', 'UPDATE - Reformatted Release Date: %s' % date_original)
			metadata.originally_available_at = date_original
			metadata.year = metadata.originally_available_at.year
		except Exception as e:
			self.log('error', 'UPDATE - Error getting release date: %s', e)
			pass

	def fetch_summary(self, html, metadata):
		self.log('info', 'UPDATE: fetch_summary CALLED')
		try:
			video_summary=html.xpath('substring-after(//*[@class="episode-description"]/p/text(), " - ")')
			self.log('info', 'UPDATE - Summary: %s', video_summary)
			metadata.summary = video_summary
		except Exception as e:
			self.log('error', 'UPDATE - Error getting description text: %s', e)
			pass

	def fetch_images(self, html, metadata):
		self.log('info', 'UPDATE: fetch_images CALLED')
		i = 0
		try:
			coverPrefs = int(Prefs['cover'])
		except ValueError:
			# an absurdly high number means "download all the things"
			coverPrefs = 10000

		valid_image_names = []

		images = html.xpath('//*[@class="episode--gallery"]//img/@src')
		self.log('info', 'UPDATE - Image URLs: "%s"' % images)

		for image in images:
			image = image.strip()
			image = 'https://fraternityx.com' + image
			if (len(image) > 0):
				valid_image_names.append(image)
				if image not in metadata.posters:
					try:
						i += 1
						metadata.posters[image] = Proxy.Preview(HTTP.Request(image), sort_order=i)
					except:
						pass

		return valid_image_names

	def update(self, metadata, media, lang):
		self.log('info', 'UPDATE CALLED')

		enclosing_directory, file_name = os.path.split(os.path.splitext(media.items[0].parts[0].file)[0])
		file_name = file_name.lower()

		if not media.items[0].parts[0].file:
			return

		file_path = media.items[0].parts[0].file
		self.log('info', 'UPDATE - File Path: %s', file_path)
		self.log('info', 'UPDATE - Video URL: %s', metadata.id)
		url = metadata.id

		# Fetch HTML
		html = HTML.ElementFromURL(url, sleep=REQUEST_DELAY)

		# Set tagline to URL
		metadata.tagline = url

		# Set additional metadata
		metadata.content_rating = 'X'
		metadata.studio = AGENT_NAME

		# Try to get the title
		try:
			self.fetch_title(html, metadata)
		except:
			pass

		# Try to get the release date
		try:
			self.fetch_date(html, metadata)
		except:
			pass

		# Try to get the summary
		try:
			self.fetch_summary(html, metadata)
		except:
			pass

		# Try to get the video images
		try:
			self.fetch_images(html, metadata)
		except:
			pass

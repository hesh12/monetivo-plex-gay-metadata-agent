# Cock Porn
import platform, sys

AGENT_NAME             = 'Cock Porn'
AGENT_VERSION          = '2020.06.21.0'
AGENT_LANGUAGES        = [Locale.Language.NoLanguage, Locale.Language.English]
AGENT_PRIMARY_PROVIDER = True
AGENT_ACCEPTS_FROM     = ['com.plexapp.agents.localmedia']
AGENT_CACHE_TIME       = CACHE_1HOUR * 24

AGENT_UTILS = None

def Start():
	Log.Info('-----------------------------------------------------------------------')
	Log.Info('[' + AGENT_NAME + '] ' + 'Starting Metadata Agent ' + AGENT_VERSION)

def ValidatePrefs():
	Log.Info('Validating Preferences')
	Log.Debug('Ouput debugging info in logs: ' + Prefs['debug'])
	Log.Info('Validation Complete')

class CockPornAgent(Agent.Movies):
	name = AGENT_NAME
	languages = AGENT_LANGUAGES
	primary_provider = AGENT_PRIMARY_PROVIDER
	accepts_from = AGENT_ACCEPTS_FROM

	def log(self, state, message, *args):
		if Prefs['debug']:
			if state == 'info':
				Log.Info('[' + AGENT_NAME + '] ' +  ' - ' + message, *args)
			elif state == 'debug':
				Log.Debug('[' + AGENT_NAME + '] ' +  ' - ' + message, *args)

	def search(self, results, media, lang):
		self.log('info', 'SEARCH CALLED v.%s', AGENT_VERSION)
		self.log('debug', 'SEARCH - Platform: %s %s', platform.system(), platform.release())
		self.log('debug', 'SEARCH - Python - %s', sys.version_info)
		self.log('debug', 'SEARCH - media.filename - %s', media.filename.split('%2F')[-1])
		self.log('debug', 'SEARCH - results - %s', results)
		self.log('debug', 'SEARCH - media.title - %s', media.title)

		results.Append(MetadataSearchResult(id=media.id, name=media.name, score = 86, lang = lang))
		self.log('debug', 'SEARCH - %s', results)
		self.log('info', 'SEARCH COMPLETE')


	def update(self, metadata, media, lang):
		self.log('info', 'UPDATE CALLED v.%s', AGENT_VERSION)
		self.log('info', 'UPDATE COMPLETE')

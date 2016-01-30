import os

from sugar import profile
from sugar import util
from sugar.activity import activity
import shutil

from color import Color

class Instance:
	key = profile.get_pubkey()
	#joyride ...
	#keyHash = util.sha_data(key)
	#8.2...
	#keyHash = util._sha_data(key)
	#keyHashPrintable = util.printable_hash(keyHash)
	nickName = profile.get_nick_name()

	colorFill = Color()
	colorFill.init_hex( profile.get_color().get_fill_color() )
	colorStroke = Color()
	colorStroke.init_hex( profile.get_color().get_stroke_color() )

	instanceId = None
	instancePath = None
	dataPath = None

	def __init__(self, ca):
		self.__class__.instanceId = ca._activity_id

		self.__class__.instancePath = os.path.join(ca.get_activity_root(), "instance")
		recreateTmp()

		self.__class__.dataPath = os.path.join(ca.get_activity_root(), "data")
		recreateData()


def recreateTmp():
	if (not os.path.exists(Instance.instancePath)):
		os.makedirs(Instance.instancePath)


def recreateData():
	if (not os.path.exists(Instance.dataPath)):
		os.makedirs(Instance.dataPath)
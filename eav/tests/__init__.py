from django.conf import settings

from utils import TestSettingsManager

mgr = TestSettingsManager()
INSTALLED_APPS = list(settings.INSTALLED_APPS)
INSTALLED_APPS.append('eav.tests')
mgr.set(INSTALLED_APPS=INSTALLED_APPS)

from .registry import *
from .limiting_attributes import *
from .data_validation import *
#from .misc_models import *
#from .queries import *
#from .forms import *
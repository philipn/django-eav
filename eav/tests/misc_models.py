from django.test import TestCase

from ..models import EnumGroup

import eav
from .models import Patient, PatientAttribute, PatientValue


class MiscModels(TestCase):

    def test_enumgroup_unicode(self):
        name = 'Yes / No'
        e = EnumGroup.objects.create(name=name)
        self.assertEqual(unicode(e), name)

    def test_attribute_help_text(self):
        desc = 'Patient Age'
        a = PatientAttribute.objects.create(name='age', description=desc, type=PatientAttribute.TYPE_INT)
        self.assertEqual(a.help_text, desc)

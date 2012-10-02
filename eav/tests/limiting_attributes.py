from django.test import TestCase

import eav
from ..registry import EavConfig

from .models import Patient, PatientAttribute, PatientValue,\
                    Encounter, EncounterAttribute, EncounterValue


class LimitingAttributes(TestCase):

    def setUp(self):
        class EncounterEavConfig(EavConfig):
            eav_attr = 'eav_field'
            eav_relation_attr = 'encounter_eav_values'

            @classmethod
            def get_attributes(cls, entity=None):
                return EncounterAttribute.objects.filter(slug__contains='a')

        eav.register(Encounter, EncounterAttribute, EncounterValue,
                     EncounterEavConfig)
        eav.register(Patient, PatientAttribute, PatientValue)

        PatientAttribute.objects.create(name='age', datatype=PatientAttribute.TYPE_INT)
        PatientAttribute.objects.create(name='height', datatype=PatientAttribute.TYPE_FLOAT)
        PatientAttribute.objects.create(name='weight', datatype=PatientAttribute.TYPE_FLOAT)

        EncounterAttribute.objects.create(name='age', datatype=EncounterAttribute.TYPE_INT)
        EncounterAttribute.objects.create(name='height', datatype=EncounterAttribute.TYPE_FLOAT)
        EncounterAttribute.objects.create(name='weight', datatype=EncounterAttribute.TYPE_FLOAT)

    def tearDown(self):
        eav.unregister(Encounter)
        eav.unregister(Patient)

    def test_get_attribute_querysets(self):
        self.assertEqual(Patient._eav_config_cls \
                                .get_attributes().count(), 3)
        self.assertEqual(Encounter._eav_config_cls \
                                .get_attributes().count(), 1)

    def test_setting_attributes(self):
        p = Patient.objects.create(name='Jon')
        e = Encounter.objects.create(patient=p, num=1)
        p.eav.age = 3
        p.eav.height = 2.3
        p.save()
        self.assertEqual(PatientValue.objects.count(), 2)
        e.eav_field.age = 4
        e.eav_field.height = 4.5
        e.save()
        self.assertEqual(EncounterValue.objects.count(), 1)
        p = Patient.objects.get(name='Jon')
        self.assertEqual(p.eav.age, 3)
        self.assertEqual(p.eav.height, 2.3)
        e = Encounter.objects.get(num=1)
        self.assertEqual(e.eav_field.age, 4)
        self.assertFalse(hasattr(e.eav_field, 'height'))

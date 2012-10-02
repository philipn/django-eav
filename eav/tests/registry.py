from django.test import TestCase

import eav
from ..registry import EavConfig

from .models import Patient, PatientAttribute, PatientValue, Encounter,\
                    EncounterAttribute, EncounterValue


class RegistryTests(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def register_encounter(self):
        class EncounterEav(EavConfig):
            eav_attr = 'eav_field'
            eav_relation_attr = 'encounter_eav_values'

            @classmethod
            def get_attributes(cls, entity=None):
                return 'testing'

        eav.register(Encounter, EncounterAttribute, EncounterValue,
                     EncounterEav)

    def test_registering_with_defaults(self):
        eav.register(Patient, PatientAttribute, PatientValue)
        self.assertTrue(hasattr(Patient, '_eav_config_cls'))
        self.assertEqual(Patient._eav_config_cls.eav_attr, 'eav')
        self.assertEqual(Patient._eav_config_cls.eav_relation_attr,
                         'eav_values')
        self.assertEqual(Patient._eav_config_cls.value_cls, PatientValue)
        self.assertEqual(Patient._eav_config_cls.attribute_cls,
                         PatientAttribute)
        eav.unregister(Patient)

    def test_registering_overriding_defaults(self):
        eav.register(Patient, PatientAttribute, PatientValue)
        self.register_encounter()
        self.assertTrue(hasattr(Patient, '_eav_config_cls'))
        self.assertEqual(Patient._eav_config_cls.eav_attr, 'eav')

        self.assertTrue(hasattr(Encounter, '_eav_config_cls'))
        self.assertEqual(Encounter._eav_config_cls.get_attributes(), 'testing')
        self.assertEqual(Encounter._eav_config_cls.eav_attr, 'eav_field')
        eav.unregister(Patient)
        eav.unregister(Encounter)

    def test_unregistering(self):
        eav.register(Patient, PatientAttribute, PatientValue)
        self.assertTrue(hasattr(Patient, '_eav_config_cls'))
        eav.unregister(Patient)
        self.assertFalse(hasattr(Patient, '_eav_config_cls'))

    def test_unregistering_unregistered_model_proceeds_silently(self):
        eav.unregister(Patient)

    def test_double_registering_model_is_harmless(self):
        eav.register(Patient, PatientAttribute, PatientValue)
        eav.register(Patient, PatientAttribute, PatientValue)
        eav.unregister(Patient)

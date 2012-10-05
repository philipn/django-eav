from datetime import datetime
try:
    from django.utils.timezone import now
except ImportError:
    now = datetime.now

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

import eav
from ..models import EnumValue, EnumGroup

from .models import Patient, PatientAttribute, PatientValue


class DataValidation(TestCase):

    def setUp(self):
        eav.register(Patient, PatientAttribute, PatientValue)

        PatientAttribute.objects.create(name='Age', datatype=PatientAttribute.TYPE_INT)
        PatientAttribute.objects.create(name='DoB', datatype=PatientAttribute.TYPE_DATE)
        PatientAttribute.objects.create(name='Height', datatype=PatientAttribute.TYPE_FLOAT)
        PatientAttribute.objects.create(name='City', datatype=PatientAttribute.TYPE_TEXT)
        PatientAttribute.objects.create(name='Pregnant?', datatype=PatientAttribute.TYPE_BOOLEAN)

    def tearDown(self):
        eav.unregister(Patient)

    def test_bad_slug(self):
        self.assertRaises(ValidationError, PatientAttribute.objects.create,
                          name='!!', datatype=PatientAttribute.TYPE_TEXT)

    def test_changing_datatypes(self):
        a = PatientAttribute.objects.create(name='Eye Color', datatype=PatientAttribute.TYPE_INT)
        a.datatype = PatientAttribute.TYPE_TEXT
        a.save()
        b = Patient.objects.create(name='Bob')
        b.eav['eye_color']='brown'
        b.save()
        a.datatype = PatientAttribute.TYPE_INT
        self.assertRaises(ValidationError, a.save)

    def test_int_validation(self):
        p = Patient.objects.create(name='Joe')
        p.eav['age'] = 'bad'
        self.assertRaises(ValidationError, p.save)
        p.eav['age'] = 15
        p.save()
        self.assertEqual(Patient.objects.get(pk=p.pk).eav['age'], 15)

    def test_date_validation(self):
        p = Patient.objects.create(name='Joe')
        p.eav['dob'] = 'bad'
        self.assertRaises(ValidationError, p.save)
        p.eav['dob'] = 15
        self.assertRaises(ValidationError, p.save)
        now_datetime = now()
        p.eav['dob'] = now_datetime
        p.save()
        self.assertEqual(Patient.objects.get(pk=p.pk).eav['dob'], now_datetime)
        self.assertEqual(Patient.objects.get(pk=p.pk).eav['dob'].date(), now_datetime.date())

    def test_float_validation(self):
        p = Patient.objects.create(name='Joe')
        p.eav['height'] = 'bad'
        self.assertRaises(ValidationError, p.save)
        p.eav['height'] = 15
        p.save()
        self.assertEqual(Patient.objects.get(pk=p.pk).eav['height'], 15)
        p.eav['height'] = '2.3'
        p.save()
        self.assertEqual(Patient.objects.get(pk=p.pk).eav['height'], 2.3)

    def test_text_validation(self):
        p = Patient.objects.create(name='Joe')
        p.eav['city'] = 5
        self.assertRaises(ValidationError, p.save)
        p.eav['city'] = 'El Dorado'
        p.save()
        self.assertEqual(Patient.objects.get(pk=p.pk).eav['city'], 'El Dorado')

    def test_bool_validation(self):
        p = Patient.objects.create(name='Joe')
        p.eav['pregnant'] = 5
        self.assertRaises(ValidationError, p.save)
        p.eav['pregnant'] = True
        p.save()
        self.assertEqual(Patient.objects.get(pk=p.pk).eav['pregnant'], True)

    def test_enum_validation(self):
        yes = EnumValue.objects.create(value='yes')
        no = EnumValue.objects.create(value='no')
        unkown = EnumValue.objects.create(value='unkown')
        green = EnumValue.objects.create(value='green')
        ynu = EnumGroup.objects.create(name='Yes / No / Unknown')
        ynu.enums.add(yes)
        ynu.enums.add(no)
        ynu.enums.add(unkown)
        PatientAttribute.objects.create(name='Fever?', datatype=PatientAttribute.TYPE_ENUM, enum_group=ynu)

        p = Patient.objects.create(name='Joe')
        p.eav['fever'] = 5
        self.assertRaises(ValidationError, p.save)
        p.eav['fever'] = object
        self.assertRaises(ValidationError, p.save)
        p.eav['fever'] = 'yes'
        self.assertRaises(ValidationError, p.save)
        p.eav['fever'] = green
        self.assertRaises(ValidationError, p.save)
        p.eav['fever'] = EnumValue(value='yes')
        self.assertRaises(ValidationError, p.save)
        p.eav['fever'] = no
        p.save()
        self.assertEqual(Patient.objects.get(pk=p.pk).eav['fever'], no)
#
    def test_enum_datatype_without_enum_group(self):
        a = PatientAttribute(name='Age Bracket', datatype=PatientAttribute.TYPE_ENUM)
        self.assertRaises(ValidationError, a.save)
        yes = EnumValue.objects.create(value='yes')
        no = EnumValue.objects.create(value='no')
        unkown = EnumValue.objects.create(value='unkown')
        ynu = EnumGroup.objects.create(name='Yes / No / Unknown')
        ynu.enums.add(yes)
        ynu.enums.add(no)
        ynu.enums.add(unkown)
        a = PatientAttribute(name='Age Bracket', datatype=PatientAttribute.TYPE_ENUM, enum_group=ynu)
        a.save()

    def test_enum_group_on_other_datatype(self):
        yes = EnumValue.objects.create(value='yes')
        no = EnumValue.objects.create(value='no')
        unkown = EnumValue.objects.create(value='unkown')
        ynu = EnumGroup.objects.create(name='Yes / No / Unknown')
        ynu.enums.add(yes)
        ynu.enums.add(no)
        ynu.enums.add(unkown)
        a = PatientAttribute(name='color', datatype=PatientAttribute.TYPE_TEXT, enum_group=ynu)
        self.assertRaises(ValidationError, a.save)

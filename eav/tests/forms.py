from datetime import datetime
try:
    from django.utils.timezone import now
except ImportError:
    now = datetime.now
from django.test import TestCase

import eav
from .models import Patient, PatientAttribute, PatientValue
from ..forms import BaseDynamicEntityForm
from ..models import EnumValue, EnumGroup

class FormTest(TestCase):
    def setUp(self):
        eav.register(Patient, PatientAttribute, PatientValue)

        PatientAttribute.objects.create(name='Age', datatype=PatientAttribute.TYPE_INT)
        PatientAttribute.objects.create(name='DoB', datatype=PatientAttribute.TYPE_DATE)
        PatientAttribute.objects.create(name='Height', datatype=PatientAttribute.TYPE_FLOAT)
        PatientAttribute.objects.create(name='City', datatype=PatientAttribute.TYPE_TEXT)
        PatientAttribute.objects.create(name='Pregnant?', datatype=PatientAttribute.TYPE_BOOLEAN)

        yes = EnumValue.objects.create(value='yes')
        no = EnumValue.objects.create(value='no')
        unkown = EnumValue.objects.create(value='unkown')
        ynu = EnumGroup.objects.create(name='Yes / No / Unknown')
        ynu.enums.add(yes)
        ynu.enums.add(no)
        ynu.enums.add(unkown)
        PatientAttribute.objects.create(name='Fever?', datatype=PatientAttribute.TYPE_ENUM, enum_group=ynu)

    def tearDown(self):
        eav.unregister(Patient)

    def test_form_validation(self):
        p = Patient.objects.create(name='Bob')
        p.eav['age'] = 2
        p.eav['dob'] = now()
        p.eav['height'] = 14.1
        p.eav['city'] = 'San Francisco'
        p.eav['pregnant'] = False
        p.eav['fever'] = EnumValue.objects.get(value='yes')
        p.save()

        # invalid age field
        data = {'age': 'abc'}
        form = BaseDynamicEntityForm(data=data, instance=p)
        self.assertFalse(form.is_valid())

        # all valid
        data = {'age': 1, 'dob_0': '2012-01-01', 'dob_1': '12:00:00',
                'height': 10.1, 'city': 'Moscow', 'pregnant': True,
                'fever': [EnumValue.objects.get(value='no').id]}
        form = BaseDynamicEntityForm(data=data, instance=p)
        self.assertTrue(form.is_valid())

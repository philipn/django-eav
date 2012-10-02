from django.db import models
from django.utils.translation import gettext_lazy as _

from eav.models import BaseAttribute, BaseValue


class Patient(models.Model):
    class Meta:
        app_label = 'eav'

    name = models.CharField(max_length=12)

    def __unicode__(self):
        return self.name

class Encounter(models.Model):
    class Meta:
        app_label = 'eav'

    num = models.PositiveSmallIntegerField()
    patient = models.ForeignKey(Patient)

    def __unicode__(self):
        return '%s: encounter num %d' % (self.patient, self.num)


class PatientAttribute(BaseAttribute):
    pass


class PatientValue(BaseValue):
    attribute = models.ForeignKey(PatientAttribute, db_index=True,
                                  verbose_name=_(u"attribute"))
    entity = models.ForeignKey(Patient, blank=False, null=False)


class EncounterAttribute(BaseAttribute):
    pass


class EncounterValue(BaseValue):
    attribute = models.ForeignKey(EncounterAttribute, db_index=True,
                                  verbose_name=_(u"attribute"))
    entity = models.ForeignKey(Encounter, blank=False, null=False)


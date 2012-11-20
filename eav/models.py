#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
#
#    This software is derived from EAV-Django originally written and
#    copyrighted by Andrey Mikhaylenko <http://pypi.python.org/pypi/eav-django>
#
#    This is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This software is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with EAV-Django.  If not, see <http://gnu.org/licenses/>.
from django.db.models.fields.related import ForeignKey, ManyToManyField,\
    OneToOneField
'''
******
models
******
This module defines the two abstract models:

* :class:`BaseValue`
* :class:`BaseAttribute`

As well as two concrete models:

* :class:`EnumValue`
* :class:`EnumGroup`

Along with the :class:`Entity` helper class.

Classes
-------
'''
from itertools import chain

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.conf import settings
from django.forms.models import BaseModelForm, BaseModelFormSet

from .validators import *
from .fields import EavSlugField, EavDatatypeField


class EnumGroup(models.Model):
    '''
    *EnumGroup* objects have just a  *name* ``CharField``.
    :class:`BaseAttribute` classes with datatype *TYPE_ENUM* have a
    ``ForeignKey`` field to *EnumGroup*.

    See :class:`EnumValue` for an example.

    '''
    name = models.CharField(_(u"name"), unique=True, max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _(u'enum group')
        verbose_name_plural = _(u'enum groups')


class EnumValue(models.Model):
    '''
    *EnumValue* objects are the value 'choices' to multiple choice
    *TYPE_ENUM* :class:`BaseAttribute` subclass objects.

    They have two fields: a *value* ``CharField`` that must be unique, and
    *group*, a ``ForeignKey`` to :class:`EnumGroup`. 

    For example:

    >>> yes = EnumValue(value='yes')
    >>> no = EnumValue(value='no')
    >>> unkown = EnumValue(value='unkown')

    >>> ynu = EnumGroup.objects.create(name='Yes / No / Unkown')
    >>> ynu.value_set.add(yes, no, unkown)

    >>> PatientAttribute.objects.create(name='Has Fever?',
    ...                          datatype=BaseAttribute.TYPE_ENUM,
    ...                          enum_group=ynu)
    '''
    value = models.CharField(_(u"value"), db_index=True,
                             unique=True, max_length=50)
    group = models.ForeignKey(EnumGroup, verbose_name=_(u"group"),
                              related_name="enums", null=True)

    def __unicode__(self):
        return self.value

    class Meta:
        verbose_name = _(u'enum value')
        verbose_name_plural = _(u'enum values')


class BaseAttribute(models.Model):
    '''
    Putting the **A** in *EAV*. This holds the attributes, or concepts.
    Examples of possible *attributes*: color, height, weight,
    number of children, number of patients, has fever?, etc...

    Each attribute has a name, and a description, along with a slug that must
    be unique.  If you don't provide a slug, a default slug (derived from
    name), will be created.

    The available datatypes are determined by the subclassing model. 

    This is an abstract model. All you have to do is subclass and register your
    concrete model. See :class:`BaseValue` for a full example.

    Examples:

    >>> PatientAttribute.objects.create(name='Height', datatype=BaseAttribute.TYPE_INT)
    <PatientAttribute: Height (Integer)>

    >>> PatientAttribute.objects.create(name='Color', datatype=BaseAttribute.TYPE_TEXT)
    <PatientAttribute: Color (Text)>

    >>> yes = EnumValue(value='yes')
    >>> no = EnumValue(value='no')
    >>> unkown = EnumValue(value='unkown')
    >>> ynu = EnumGroup.objects.create(name='Yes / No / Unkown')
    >>> ynu.enums.add(yes, no, unkown)
    >>> PatientAttribute.objects.create(name='Has Fever?',
    ...                          datatype=BaseAttribute.TYPE_ENUM,
    ...                          enum_group=ynu)
    <PatientAttribute: Has Fever? (Multiple Choice)>

    .. warning:: Once an attribute has been used by an entity, you cannot
                 change it's datatype.
    '''

    TYPE_TEXT = 'text'
    TYPE_FLOAT = 'float'
    TYPE_INT = 'int'
    TYPE_DATE = 'date'
    TYPE_BOOLEAN = 'bool'
    TYPE_ENUM = 'enum'

    class Meta:
        abstract = True
        ordering = ['name']
        unique_together = ('site', 'slug')
        verbose_name = _(u'attribute')
        verbose_name_plural = _(u'attributes')

    name = models.CharField(_(u"name"), max_length=100,
                            help_text=_(u"User-friendly attribute name"))

    site = models.ForeignKey(Site, verbose_name=_(u"site"),
                             default=Site.objects.get_current)

    slug = EavSlugField(_(u"slug"), max_length=100, db_index=True,
                          editable=False,
                          help_text=_(u"Short unique attribute label"))

    description = models.CharField(_(u"description"), max_length=256,
                                     blank=True, null=True,
                                     help_text=_(u"Short description"))

    enum_group = models.ForeignKey(EnumGroup, verbose_name=_(u"choice group"),
                                   blank=True, null=True)

    @property
    def help_text(self):
        return self.description

    datatype = EavDatatypeField(_(u"data type"), max_length=8)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    def get_value_cls(self):
        return self.parent_model._eav_config_cls.value_cls

    def get_validators(self):
        '''
        Returns the appropriate validator function from :mod:`~eav.validators`
        as a list (of length one) for the datatype.

        .. note::
           The reason it returns it as a list, is eventually we may want this
           method to look elsewhere for additional attribute specific
           validators to return as well as the default, built-in one.
        '''
        DATATYPE_VALIDATORS = {
            'text': validate_text,
            'float': validate_float,
            'int': validate_int,
            'date': validate_date,
            'bool': validate_bool,
            'enum': validate_enum,
        }

        validation_function = DATATYPE_VALIDATORS.get(self.datatype, None)
        if validation_function:
            return [validation_function]
        return []

    def validate_value(self, value):
        '''
        Check *value* against the validators returned by
        :meth:`get_validators` for this attribute.
        '''
        for validator in self.get_validators():
            validator(value)
        if self.datatype == self.TYPE_ENUM:
            if value not in self.enum_group.enums.all():
                raise ValidationError(_(u"%(enum)s is not a valid choice "
                                        u"for %(attr)s") % \
                                       {'enum': value, 'attr': self})

    def save(self, *args, **kwargs):
        '''
        Saves the attribute and auto-generates a slug field if one wasn't
        provided.
        '''

        self.full_clean()
        super(BaseAttribute, self).save(*args, **kwargs)

    def clean(self):
        '''
        Validates the attribute.  Will raise ``ValidationError`` if
        the attribute's datatype is *TYPE_ENUM* and enum_group is not set,
        or if the attribute is not *TYPE_ENUM* and the enum group is set.
        '''
        self.slug = EavSlugField.create_slug_from_name(self.name)
        if not self.slug:
            raise ValidationError(_(u"The attribute name is invalid."))

        if self.datatype == self.TYPE_ENUM and not self.enum_group:
            raise ValidationError(_(
                u"You must set the choice group for multiple choice " \
                u"attributes"))

        if self.datatype != self.TYPE_ENUM and self.enum_group:
            raise ValidationError(_(
                u"You can only assign a choice group to multiple choice " \
                u"attributes"))

    def get_choices(self):
        '''
        Returns a query set of :class:`EnumValue` objects for this attribute.
        Returns None if the datatype of this attribute is not *TYPE_ENUM*.
        '''
        if not self.datatype == self.TYPE_ENUM:
            return None
        return self.enum_group.enums.all()

    def _formset_has_changed(self, formset):
        # Note: in Django 1.4 this is built in
        return any(form.has_changed() for form in formset)

    def value_has_changed(self, old_value, new_value):
        if isinstance(new_value, (BaseModelForm,)):
            return new_value.has_changed()
        if isinstance(new_value, (BaseModelFormSet,)):
            return self._formset_has_changed(new_value)

        if self.datatype in (self.TYPE_BOOLEAN, self.TYPE_DATE,
                             self.TYPE_FLOAT, self.TYPE_INT, self.TYPE_TEXT):
            return old_value != new_value
        if self.datatype in (self.TYPE_ENUM,):
            return set(old_value.all()) != set(new_value)
        return True

    def save_value(self, entity, value):
        '''
        Called with *entity*, any django object registered with eav, and
        *value*, the :class:`Value` this attribute for *entity* should
        be set to.

        If a :class:`Value` object for this *entity* and attribute doesn't
        exist, one will be created.
        '''
        try:
            value_obj = self.get_value_cls().objects.get(entity=entity,
                                           attribute=self)
        except self.get_value_cls().DoesNotExist:
            value_obj = self.get_value_cls()(entity=entity, attribute=self)

        if not value_obj.pk or self.value_has_changed(value_obj.value, value):
            if isinstance(value, (BaseModelForm, BaseModelFormSet)):
                value = value.save()
            if self.datatype == self.TYPE_ENUM:
                already_saved = True
                if value is None:
                    value = []
                elif not hasattr(value, '__iter__'):
                    value = [value]

            if value_obj.is_m2m():
                # For compatibility with versioning, we need to save M2M fields
                # before setting their value, since setting them will save the
                # M2M relation
                value_obj.save()
            value_obj.value = value
            if not value_obj.is_m2m():
                value_obj.save()

    def get_datatype_display(self):
        value_field = 'value_' + self.datatype
        return self.get_value_cls()._meta.get_field(value_field).verbose_name

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.get_datatype_display())


class BaseValue(models.Model):
    """
    Abstract model for building values. To add custom value types, subclass
    this, add an "attribute" field that is a ForeignKey pointing at your
    attribute model, add an "entity" field that is a ForeignKey pointing at
    your entity model, define your custom types and register it like this:
        class PageAttribute(BaseAttribute):
            pass

        class PageValue(BaseValue"):
            attribute = models.ForeignKey(PageAttribute, blank=False,
                                          null=False)
            entity = models.ForeignKey(Page, blank=False, null=False)
            value_author = models.ForeignKey(User, blank=True, null=True)

        eav.register(Page, PageAttribute, PageValue)
    """
    value_text = models.TextField(_(u"text"), blank=True, null=True,
                                  db_index=True)
    value_float = models.FloatField(_(u"floating point"), blank=True,
                                    null=True, db_index=True)
    value_int = models.IntegerField(_(u"integer"), blank=True, null=True,
                                    db_index=True)
    value_date = models.DateTimeField(_(u"date and time"), blank=True,
                                      null=True, db_index=True)
    value_bool = models.NullBooleanField(_(u"Yes / No"), blank=True,
                                         null=True, db_index=True)
    value_enum = models.ManyToManyField(EnumValue,
                                        verbose_name=_(u"multiple choice"),
                                        blank=True, null=True,
                                        related_name='eav_%(class)ss')

    def save(self, *args, **kwargs):
        '''
        Validate and save this value
        '''
        self.full_clean()
        super(BaseValue, self).save(*args, **kwargs)

    @classmethod
    def get_datatype_choices(cls):
        value_field_prefix = 'value_'
        fields = chain(cls._meta.fields, cls._meta.many_to_many)
        value_fields = [f for f in fields
                        if f.name.startswith(value_field_prefix)]
        return [(f.name[len(value_field_prefix):], f.verbose_name)
                for f in value_fields]

    def _get_value(self):
        '''
        Return the python object this value is holding
        '''
        return getattr(self, 'value_%s' % self.attribute.datatype)

    def _set_value(self, new_value):
        '''
        Set the object this value is holding
        '''
        setattr(self, 'value_%s' % self.attribute.datatype, new_value)

    value = property(_get_value, _set_value)

    def is_m2m(self):
        '''
        Returns True if this value's data field is a m2m.
        '''
        data_field_name = 'value_%s' % self.attribute.datatype
        data_field = self._meta.get_field(data_field_name)
        return isinstance(data_field, ManyToManyField)

    def __unicode__(self):
        return u"%s - %s: \"%s\"" % (self.entity, self.attribute.name,
                                     self.value)

    class Meta:
        abstract = True
        verbose_name = _(u'value')
        verbose_name_plural = _(u'values')


class Entity(object):
    '''
    The helper class that will be attached to any entity registered with
    eav.
    '''

    def __init__(self, instance):
        '''
        Set self.model equal to the instance of the model that we're attached
        to.  Also, store the content type of that instance.
        '''
        self.eav_attributes = {}
        self.model = instance

    def __getitem__(self, name):
        '''
        Tha magic getitem helper.  This is called whenevery you do
        this_instance[<whatever>]
        '''
        try:
            attribute = self.get_attribute_by_slug(name)
        except self.model._eav_config_cls.attribute_cls.DoesNotExist:
            raise KeyError(_(u"%(obj)s has no EAV attribute named " \
                                   u"'%(attr)s'") % \
                                 {'obj': self.model, 'attr': name})
        try:
            return self.get_value_by_attribute(attribute).value
        except self.model._eav_config_cls.value_cls.DoesNotExist:
            raise KeyError

    def __contains__(self, name):
        try:
            self.__getitem__(name)
            return True
        except KeyError:
            return False

    def __setitem__(self, name, value):
        self.eav_attributes[name] = value

    def get(self, name, default):
        if name in self.eav_attributes:
            return self.eav_attributes[name]
        try:
            return self.__getitem__(name)
        except KeyError:
            return default

    def get_all_attributes(self):
        '''
        Return a query set of all :class:`BaseAttribute` objects that can be
        set for this entity.
        '''
        # cache result
        if not hasattr(self, '_attributes_qs'):
            self._attributes_qs = self.model._eav_config_cls.get_attributes(
                                                            entity=self.model)
        return self._attributes_qs

    def get_attributes_and_values(self):
        return dict( (v.attribute.slug, v.value) for v in self.get_values() )

    def save(self):
        '''
        Saves all the EAV values that have been set on this entity.
        '''
        for attribute in self.get_all_attributes():
            if attribute.slug in self.eav_attributes:
                attribute_value = self.eav_attributes[attribute.slug]
                attribute.save_value(self.model, attribute_value)

    def validate_attributes(self):
        '''
        Called before :meth:`save`, first validate all the entity values to
        make sure they can be created / saved cleanly.

        Raise ``ValidationError`` if they can't be.
        '''
        for attribute in self.get_all_attributes():
            value = self.get(attribute.slug, None)
            if value is not None:
                try:
                    attribute.validate_value(value)
                except ValidationError, e:
                    raise ValidationError(_(u"%(attr)s EAV field %(err)s") % \
                                            {'attr': attribute.slug,
                                             'err': e})

    def get_values(self):
        '''
        Get all set :class:`Value` objects for self.model
        '''
        return self.model._eav_config_cls.value_cls.objects.filter(
                                            entity=self.model).select_related()

    def get_all_attribute_slugs(self):
        '''
        Returns a list of slugs for all attributes available to this entity.
        '''
        # cache result
        if not hasattr(self, '_attribute_slugs'):
            self._attribute_slugs = self.get_all_attributes().values_list(
                                                            'slug', flat=True)
        return self._attribute_slugs

    def get_attribute_by_slug(self, slug):
        '''
        Returns a single :class:`BaseAttribute` with *slug*
        '''
        return self.get_all_attributes().get(slug=slug)

    def get_value_by_attribute(self, attribute):
        '''
        Returns a single :class:`Value` for *attribute*
        '''
        return self.get_values().get(attribute=attribute)

    def __iter__(self):
        '''
        Iterate over set eav values.

        This would allow you to do:

        >>> for i in m.eav: print i  # doctest: +SKIP
        '''
        return iter(self.get_values())

    @staticmethod
    def post_save_handler(sender, *args, **kwargs):
        '''
        Post save handler attached to self.model.  Calls :meth:`save` when
        the model instance we are attached to is saved.
        '''
        instance = kwargs['instance']
        entity = getattr(instance, instance._eav_config_cls.eav_attr)
        entity.save()

    @staticmethod
    def pre_save_handler(sender, *args, **kwargs):
        '''
        Pre save handler attached to self.model.  Called before the
        model instance we are attached to is saved. This allows us to call
        :meth:`validate_attributes` before the entity is saved.
        '''
        instance = kwargs['instance']
        entity = getattr(kwargs['instance'], instance._eav_config_cls.eav_attr)
        entity.validate_attributes()


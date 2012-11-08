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
from django.forms.fields import TypedChoiceField
'''
#####
forms
#####

The forms used for admin integration

Classes
-------
'''
import re
from copy import deepcopy

from django.forms import NullBooleanField, CharField, DateTimeField,\
                         FloatField, IntegerField, ModelForm,\
                         ModelMultipleChoiceField, Field, ValidationError
from django.forms import Widget
from django.forms.widgets import CheckboxSelectMultiple, SplitDateTimeWidget
from django.forms.models import ModelChoiceField, inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode
from django.template.loader import render_to_string


# convert model's name to lowercase with underscores: MyThing -> my_thing
get_css_class = lambda class_name: re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', class_name).lower().strip().replace(' ', '_')


def form_as_single_field(FormClass, instance, prefix):
    class ModelFormWidget(Widget):
        """ Returns a form for a FK'd instance as a single widget for display
        in the parent form.
        """
        def render(self, name, value, attrs=None):
            form = FormClass(instance=instance, prefix=prefix)
            is_formset = hasattr(form, 'forms')
            if is_formset:
                d = {'formset': form,
                     'css_class': get_css_class(FormClass.model.__name__)
                     }
                return render_to_string('eav/formset.html', d)
            return form.as_p()

        def value_from_datadict(self, data, files, name):
            return FormClass(instance=instance, data=data, prefix=prefix)

        def _media(self):
            return FormClass().media
        media = property(_media)

    class ModelField(Field):
        widget = ModelFormWidget

        def clean(self, value):
            if not value.is_valid():
                raise ValidationError(self.error_messages['invalid'])
            return value

    return ModelField()


class UTF8FieldNamesMixin(object):
    """
    Form mixin that fixes an issue with the default implementation and allows
    for UTF-8 encoded field names, not just ASCII.
    """
    def add_prefix(self, field_name):
        prefix = super(UTF8FieldNamesMixin, self).add_prefix(field_name)
        return smart_unicode(prefix)


class MultipleChoiceField(ModelMultipleChoiceField):
    widget = CheckboxSelectMultiple


class SplitDateTimeField(DateTimeField):
    widget = SplitDateTimeWidget


class BaseDynamicEntityForm(UTF8FieldNamesMixin, ModelForm):
    '''
    ModelForm for entity with support for EAV attributes. Form fields are
    created on the fly depending on Schema defined for given entity instance.
    If no schema is defined (i.e. the entity instance has not been saved yet),
    only static fields are used. However, on form validation the schema will be
    retrieved and EAV fields dynamically added to the form, so when the
    validation is actually done, all EAV fields are present in it (unless
    Rubric is not defined).
    '''

    FIELD_CLASSES = {
        'text': CharField,
        'float': FloatField,
        'int': IntegerField,
        'date': SplitDateTimeField,
        'bool': NullBooleanField,
        'enum': MultipleChoiceField,
    }

    def __init__(self, data=None, *args, **kwargs):
        super(BaseDynamicEntityForm, self).__init__(data, *args, **kwargs)
        config_cls = self.instance._eav_config_cls
        self.entity = getattr(self.instance, config_cls.eav_attr)
        self._build_dynamic_fields()
        keyOrder = [s.encode('utf-8')
                    for s in self.entity.get_all_attribute_slugs()]
        self.fields.keyOrder = [s for s in keyOrder if s in self.fields]

    def _build_dynamic_fields(self):
        # reset form fields
        self.fields = deepcopy(self.base_fields)

        for v in self.entity.get_values():
            value = v.value
            attribute = v.attribute
            self.create_form_fields_for_attribute(attribute, value)

    def get_field_class_for_type(self, type):
        custom_fields = getattr(self, 'CUSTOM_FIELD_CLASSES', {})
        if type in custom_fields:
            return custom_fields[type]
        return self.FIELD_CLASSES[type]

    def create_form_fields_for_attribute(self, attribute, value):
        datatype = attribute.datatype
        field_name = attribute.slug.encode('utf-8')
        FieldOrForm = self.get_field_class_for_type(datatype)
        is_form = hasattr(FieldOrForm, 'as_table')
        if is_form:
            # Assume this is for a FK'd instance, construct its form
            self.fields[field_name] = form_as_single_field(FieldOrForm,
                                        instance=value, prefix=field_name)
        else:
            # Just a regular single field
            defaults = {
                'label': attribute.name.capitalize(),
                'help_text': attribute.help_text,
                'validators': attribute.get_validators(),
                'required': False,
            }

            if datatype == attribute.TYPE_ENUM:
                # for enum enough standard validator
                defaults['validators'] = []

                choices  = attribute.get_choices()
                defaults.update({
                                 'queryset': choices,
                                 })

                if value:
                    defaults.update({'initial': value.all()})

            self.fields[field_name] = FieldOrForm(**defaults)

            # fill initial data (if attribute was already defined)
            if value and not datatype == attribute.TYPE_ENUM: #enum  done above
                self.initial[field_name] = value

    def save(self, commit=True):
        """
        Saves this ``form``'s cleaned_data into model instance
        ``self.instance`` and related EAV attributes.

        Returns ``instance``.
        """

        if self.errors:
            raise ValueError(_(u"The %s could not be saved because the data "
                             u"didn't validate.") % \
                             self.instance._meta.object_name)

        # create entity instance, don't save yet
        instance = super(BaseDynamicEntityForm, self).save(commit=False)

        # assign attributes
        for attribute in self.entity.get_all_attributes():
            field_name = attribute.slug.encode('utf-8')
            if field_name not in self.cleaned_data:
                continue
            value = self.cleaned_data.get(field_name)
            if attribute.datatype == attribute.TYPE_ENUM:
                if value is None:
                    value = []

            self.entity[attribute.slug] = value

        # save entity and its attributes
        if commit:
            instance.save()

        return instance

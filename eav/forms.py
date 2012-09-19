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

from django.forms import BooleanField, CharField, DateTimeField, FloatField, \
                         IntegerField, ModelForm, ChoiceField, \
                         Field, ValidationError
from django.forms import Widget
from django.forms.models import ModelChoiceField, inlineformset_factory
from django.contrib.admin.widgets import AdminSplitDateTime
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from models import PageLink, WeeklySchedule, WeeklyTimeBlock


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

    class ModelField(Field):
        widget = ModelFormWidget

        def clean(self, value):
            if not value.is_valid():
                raise ValidationError(self.error_messages['invalid'])
            return value

    return ModelField()


class PageLinkForm(ModelForm):
    class Meta:
        model = PageLink


WeeklyTimeBlockFormSet = inlineformset_factory(WeeklySchedule, WeeklyTimeBlock,
                                               extra=7)


class WeeklyScheduleForm(WeeklyTimeBlockFormSet):
    def save(self, commit=True):
        self.instance.save()
        super(WeeklyScheduleForm, self).save(commit)
        return self.instance

    def as_p(self):
        return 


class BaseDynamicEntityForm(ModelForm):
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
        'date': DateTimeField,
        'bool': BooleanField,
        'enum': ChoiceField,
        'page': PageLinkForm,
        'schedule': WeeklyScheduleForm,
    }

    def __init__(self, data=None, *args, **kwargs):
        super(BaseDynamicEntityForm, self).__init__(data, *args, **kwargs)
        config_cls = self.instance._eav_config_cls
        self.entity = getattr(self.instance, config_cls.eav_attr)
        self._build_dynamic_fields()

    def _build_dynamic_fields(self):
        # reset form fields
        self.fields = deepcopy(self.base_fields)

        for v in self.entity.get_values():
            value = v.value
            attribute = v.attribute
            self.create_form_fields_for_attribute(attribute, value)
    
    def create_form_fields_for_attribute(self, attribute, value):
        datatype = attribute.datatype
        FieldOrForm = self.FIELD_CLASSES[datatype]
        is_form = hasattr(FieldOrForm, 'as_table')
        if is_form:
            # Assume this is for a FK'd instance, construct its form
            self.fields[attribute.slug] = form_as_single_field(FieldOrForm,
                                        instance=value, prefix=attribute.slug)
        else:
            # Just a regular single field
            defaults = {
                'label': attribute.name.capitalize(),
                'required': attribute.required,
                'help_text': attribute.help_text,
                'validators': attribute.get_validators(),
            }

            if datatype == attribute.TYPE_ENUM:
                # for enum enough standard validator
                defaults['validators'] = []

                enums = attribute.get_choices() \
                                 .values_list('id', 'value')

                choices = [('', '-----')] + list(enums)

                defaults.update({'choices': choices})
                if value:
                    defaults.update({'initial': value.pk})

            elif datatype == attribute.TYPE_DATE:
                defaults.update({'widget': AdminSplitDateTime})
            elif datatype == attribute.TYPE_OBJECT:
                return

            self.fields[attribute.slug] = FieldOrForm(**defaults)

            # fill initial data (if attribute was already defined)
            if value and not datatype == attribute.TYPE_ENUM: #enum  done above
                self.initial[attribute.slug] = value

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
            if attribute.slug not in self.cleaned_data:
                continue
            value = self.cleaned_data.get(attribute.slug)
            if attribute.datatype == attribute.TYPE_ENUM:
                if value:
                    value = attribute.enum_group.enums.get(pk=value)
                else:
                    value = None

            setattr(self.entity, attribute.slug, value)

        # save entity and its attributes
        if commit:
            instance.save()

        return instance

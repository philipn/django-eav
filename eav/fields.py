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
******
fields
******

Contains two custom fields:

* :class:`EavSlugField`
* :class:`EavDatatypeField`

Classes
-------
'''

import re

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.template.defaultfilters import stringfilter


def slugify(value):
    """
    Normalizes attribute name for db lookup

    Args:
        value: String or unicode object to normalize.
    Returns:
        Lowercase string with special characters removed.
    """

    # normalize unicode
    import unicodedata
    value = unicodedata.normalize('NFKD', unicode(value))

    # remove non-{word,space} characters
    misc_characters = re.compile('[^\w\s]', re.UNICODE)
    value = re.sub(misc_characters, '', value)
    value = value.strip()
    value = re.sub('[_\s]+', '_', value)

    return value.lower()
slugify = stringfilter(slugify)

class EavSlugField(models.SlugField):
    '''
    The slug field used by :class:`~eav.models.BaseAttribute`
    '''

    @staticmethod
    def create_slug_from_name(name):
        '''
        Creates a slug based on the name
        '''
        return slugify(name)


class EavDatatypeField(models.CharField):
    '''
    The type field used by :class:`~eav.models.BaseAttribute`
    '''

    def validate(self, value, instance):
        '''
        Raise ``ValidationError`` if they try to change the type of an
        :class:`~eav.models.BaseAttribute` that is already used by
        :class:`~eav.models.Value` objects.
        '''
        super(EavDatatypeField, self).validate(value, instance)
        if not instance.pk:
            return
        if instance.value_set.count():
            raise ValidationError(_(u"You cannot change the type of an "
                                    u"attribute that is already in use."))



try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], ["^eav\.fields\.EavSlugField"])
    add_introspection_rules([], ["^eav\.fields\.EavDatatypeField"])

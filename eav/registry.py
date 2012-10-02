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
########
registry
########

This contains the registry classes

Classes
-------
'''

from django.db.models.signals import post_init, pre_save, post_save
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from .models import Entity

class EavConfig(object):
    '''
    The default EevConfig class used if it is not overriden on registration.
    This is where all the default eav attribute names are defined.
    '''

    eav_attr = 'eav'
    eav_relation_attr = 'eav_values'

    @classmethod
    def get_attributes(cls, entity=None):
        '''
        By default, all model-appropriate attribute object apply to an entity,
        unless you provide a custom EavConfig class overriding this.
        '''
        return cls.attribute_cls.objects.all()

class Registry(object):
    '''
    Handles registration through the
    :meth:`register` and :meth:`unregister` methods.
    '''

    @staticmethod
    def register(model_cls, attribute_cls, value_cls, config_cls=None):
        '''
        Registers *model_cls* and corresponding *attribute_cls* and *value_cls*
        with eav. You can pass an optional *config_cls* to override the
        EavConfig defaults.

        .. note::
           Multiple registrations for the same entity are harmlessly ignored.
        '''
        if hasattr(model_cls, '_eav_config_cls'):
            return

        if config_cls is EavConfig or config_cls is None:
            config_cls = type("%sConfig" % model_cls.__name__,
                              (EavConfig,), {})

        config_cls.attribute_cls = attribute_cls
        config_cls.value_cls = value_cls
        attribute_cls.parent_model = model_cls

        # set _eav_config_cls on the model so we can access it there
        setattr(model_cls, '_eav_config_cls', config_cls)

        reg = Registry(model_cls)
        reg._register_self()

    @staticmethod
    def unregister(model_cls):
        '''
        Unregisters *model_cls* with eav.

        .. note::
           Unregistering a class not already registered is harmlessly ignored.
        '''
        if not getattr(model_cls, '_eav_config_cls', None):
            return
        reg = Registry(model_cls)
        reg._unregister_self()

        delattr(model_cls, '_eav_config_cls')

    @staticmethod
    def attach_eav_attr(sender, *args, **kwargs):
        '''
        Attach EAV Entity toolkit to an instance after init.
        '''
        instance = kwargs['instance']
        config_cls = instance.__class__._eav_config_cls
        setattr(instance, config_cls.eav_attr, Entity(instance))

    def __init__(self, model_cls):
        '''
        Set the *model_cls* and its *config_cls*
        '''
        self.model_cls = model_cls
        self.config_cls = model_cls._eav_config_cls

    def _attach_signals(self):
        '''
        Attach all signals for eav
        '''
        post_init.connect(Registry.attach_eav_attr, sender=self.model_cls)
        pre_save.connect(Entity.pre_save_handler, sender=self.model_cls)
        post_save.connect(Entity.post_save_handler, sender=self.model_cls)

    def _detach_signals(self):
        '''
        Detach all signals for eav
        '''
        post_init.disconnect(Registry.attach_eav_attr, sender=self.model_cls)
        pre_save.disconnect(Entity.pre_save_handler, sender=self.model_cls)
        post_save.disconnect(Entity.post_save_handler, sender=self.model_cls)

    def _alias_entity_related_name(self):
        '''
        Alias the entity's related name so it can be standard.
        '''
        rel_field = self.config_cls.eav_relation_attr.lower()
        related_name = self.config_cls.value_cls.entity.field.related_query_name()

        def get_eav_values(cls):
            return getattr(cls, related_name)

        setattr(self.model_cls, rel_field, property(get_eav_values))

    def _unalias_entity_related_name(self):
        rel_field = self.config_cls.eav_relation_attr.lower()
        delattr(self.model_cls, rel_field)

    def _alias_attribute_related_name(self):
        '''
        Alias attribute's value_set to whatever the real related name is.
        '''
        related_name = self.config_cls.value_cls.attribute.field.related_query_name()
        related_name += '_set'

        def get_eav_values(cls):
            return getattr(cls, related_name)

        setattr(self.config_cls.attribute_cls, 'value_set', property(get_eav_values))

    def _unalias_attribute_related_name(self):
        delattr(self.config_cls.attribute_cls, 'value_set')

    def _register_self(self):
        '''
        Call the necessary registration methods
        '''
        self._attach_signals()
        self._alias_entity_related_name()
        self._alias_attribute_related_name()

    def _unregister_self(self):
        '''
        Call the necessary unregistration methods
        '''
        self._detach_signals()
        self._unalias_entity_related_name()
        self._unalias_attribute_related_name()

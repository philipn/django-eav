"""
This contains the registry classes

Classes
-------
"""

from django.db.models.signals import post_init, pre_save, post_save

from .managers import EntityManager
from .models import Entity, Attribute


class EavConfig(object):
    """
    The default EevConfig class used if it is not overriden on registration.
    This is where all the default eav attribute names are defined.
    """

    manager_attr = 'objects'
    manager_only = False
    eav_attr = 'eav'

    @classmethod
    def get_attributes(cls, entity=None):
        """
        By default, all :class:`~eav.models.Attribute` object apply to an
        entity, unless you provide a custom EavConfig class overriding this.
        """
        return Attribute.on_site.all()


class Registry(object):
    """
    Handles registration through the
    :meth:`register` and :meth:`unregister` methods.
    """

    @staticmethod
    def register(model_cls, config_cls=None):
        """
        Registers *model_cls* with eav. You can pass an optional *config_cls*
        to override the EavConfig defaults.

        .. note::
           Multiple registrations for the same entity are harmlessly ignored.
        """
        if hasattr(model_cls, '_eav_config_cls'):
            return

        if config_cls is EavConfig or config_cls is None:
            config_cls = type("%sConfig" % model_cls.__name__,
                              (EavConfig,), {})

        # set _eav_config_cls on the model so we can access it there
        setattr(model_cls, '_eav_config_cls', config_cls)

        reg = Registry(model_cls)
        reg._register_self()

    @staticmethod
    def unregister(model_cls):
        """
        Unregisters *model_cls* with eav.

        .. note::
           Unregistering a class not already registered is harmlessly ignored.
        """
        if not getattr(model_cls, '_eav_config_cls', None):
            return
        reg = Registry(model_cls)
        reg._unregister_self()

        delattr(model_cls, '_eav_config_cls')

    @staticmethod
    def attach_eav_attr(sender, *args, **kwargs):
        """
        Attache EAV Entity toolkit to an instance after init.
        """
        instance = kwargs['instance']
        config_cls = instance.__class__._eav_config_cls
        setattr(instance, config_cls.eav_attr, Entity(instance))

    def __init__(self, model_cls):
        """
        Set the *model_cls* and its *config_cls*
        """
        self.model_cls = model_cls
        self.config_cls = model_cls._eav_config_cls

    def _attach_manager(self):
        """
        Attach the manager to *manager_attr* specified in *config_cls*
        """
        # save the old manager if the attribute name conflict with the new one
        if hasattr(self.model_cls, self.config_cls.manager_attr):
            mgr = getattr(self.model_cls, self.config_cls.manager_attr)
            self.config_cls.old_mgr = mgr

        # attache the new manager to the model
        mgr = EntityManager()
        mgr.contribute_to_class(self.model_cls, self.config_cls.manager_attr)

    def _detach_manager(self):
        """
        Detach the manager, and reatach the previous manager (if there was one)
        """
        delattr(self.model_cls, self.config_cls.manager_attr)
        if hasattr(self.config_cls, 'old_mgr'):
            self.config_cls.old_mgr \
                .contribute_to_class(self.model_cls,
                                     self.config_cls.manager_attr)

    def _attach_signals(self):
        """
        Attach all signals for eav
        """
        post_init.connect(Registry.attach_eav_attr, sender=self.model_cls)
        pre_save.connect(Entity.pre_save_handler, sender=self.model_cls)
        post_save.connect(Entity.post_save_handler, sender=self.model_cls)

    def _detach_signals(self):
        """
        Detach all signals for eav
        """
        post_init.disconnect(Registry.attach_eav_attr, sender=self.model_cls)
        pre_save.disconnect(Entity.pre_save_handler, sender=self.model_cls)
        post_save.disconnect(Entity.post_save_handler, sender=self.model_cls)

    def _register_self(self):
        """
        Call the necessary registration methods
        """
        self._attach_manager()

        if not self.config_cls.manager_only:
            self._attach_signals()

    def _unregister_self(self):
        """
        Call the necessary unregistration methods
        """
        self._detach_manager()

        if not self.config_cls.manager_only:
            self._detach_signals()

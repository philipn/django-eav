"""
Custom haystack search index for indexing models with eav data.
"""

from haystack import indexes
from .models import Attribute

class EAVIndex(indexes.ModelSearchIndex):
    attribute_class = Attribute
    
    def get_fields(self, *args, **kwargs):
        """
        Adds the eav fields.
        """
        final_fields = super(EAVIndex, self).get_fields(*args, **kwargs)
        fields = kwargs.get('fields')
        excludes = kwargs.get('excludes')
        
        attribute_class = self.attribute_class or Attribute
        model_attributes = attribute_class.get_for_model(self.model)
        searchable_attributes = model_attributes.filter(searchable=True)

        for attr in searchable_attributes:
            if attr.name in self.fields:
                continue
            if excludes and attr.name in excludes:
                continue
            
            index_field_class = index_field_from_eav_field(attr)
            field_kwargs = self.extra_field_kwargs
            field_kwargs.update({'model_attr': attr.name})
            final_fields[attr.name] = index_field_class(**field_kwargs)
            final_fields[attr.name].set_instance_name(self.get_index_fieldname(attr))

            
def index_field_from_eav_field(f, default=indexes.CharField):
    """
    Returns the Haystack field type that would likely be associated with each
    Django type.
    """
    result = default

    if f.datatype == Attribute.TYPE_DATE:
        result = indexes.DateTimeField
    elif f.datatype == Attribute.TYPE_BOOLEAN:
        result = indexes.BooleanField
    elif f.datatype == Attribute.TYPE_FLOAT:
        result = indexes.FloatField
    elif f.datatype == Attribute.TYPE_INT:
        result = indexes.IntegerField

    return result

            

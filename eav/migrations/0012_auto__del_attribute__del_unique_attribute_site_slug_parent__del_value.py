# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Attribute', fields ['site', 'slug', 'parent']
        db.delete_unique('eav_attribute', ['site_id', 'slug', 'parent_id'])

        # Deleting model 'Attribute'
        db.delete_table('eav_attribute')

        # Deleting model 'Value'
        db.delete_table('eav_value')

    def backwards(self, orm):
        # Adding model 'Attribute'
        db.create_table('eav_attribute', (
            ('description', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('enum_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eav.EnumGroup'], null=True, blank=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datatype', self.gf('eav.fields.EavDatatypeField')(max_length=8)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('slug', self.gf('eav.fields.EavSlugField')(max_length=50)),
        ))
        db.send_create_signal('eav', ['Attribute'])

        # Adding unique constraint on 'Attribute', fields ['site', 'slug', 'parent']
        db.create_unique('eav_attribute', ['site_id', 'slug', 'parent_id'])

        # Adding model 'Value'
        db.create_table('eav_value', (
            ('value_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('entity_id', self.gf('django.db.models.fields.IntegerField')()),
            ('value_float', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('value_bool', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eav.Attribute'])),
            ('value_enum', self.gf('django.db.models.fields.related.ForeignKey')(related_name='eav_values', null=True, to=orm['eav.EnumValue'], blank=True)),
            ('value_int', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('entity_ct', self.gf('django.db.models.fields.related.ForeignKey')(related_name='value_entities', to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('eav', ['Value'])

    models = {
        'eav.enumgroup': {
            'Meta': {'object_name': 'EnumGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'eav.enumvalue': {
            'Meta': {'object_name': 'EnumValue'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'enums'", 'null': 'True', 'to': "orm['eav.EnumGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['eav']
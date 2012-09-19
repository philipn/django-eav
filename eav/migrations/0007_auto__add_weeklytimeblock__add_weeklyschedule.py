# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'WeeklyTimeBlock'
        db.create_table('eav_weeklytimeblock', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('week_day', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('start_time', self.gf('django.db.models.fields.TimeField')()),
            ('end_time', self.gf('django.db.models.fields.TimeField')()),
            ('schedule', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['eav.WeeklySchedule'])),
        ))
        db.send_create_signal('eav', ['WeeklyTimeBlock'])

        # Adding model 'WeeklySchedule'
        db.create_table('eav_weeklyschedule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('eav', ['WeeklySchedule'])

    def backwards(self, orm):
        # Deleting model 'WeeklyTimeBlock'
        db.delete_table('eav_weeklytimeblock')

        # Deleting model 'WeeklySchedule'
        db.delete_table('eav_weeklyschedule')

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'eav.attribute': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('site', 'slug', 'parent'),)", 'object_name': 'Attribute'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datatype': ('eav.fields.EavDatatypeField', [], {'max_length': '6'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'display_in_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enum_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eav.EnumGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'searchable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'slug': ('eav.fields.EavSlugField', [], {'max_length': '50'})
        },
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
        },
        'eav.pagelink': {
            'Meta': {'object_name': 'PageLink'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'eav.value': {
            'Meta': {'object_name': 'Value'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eav.Attribute']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'entity_ct': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'value_entities'", 'to': "orm['contenttypes.ContentType']"}),
            'entity_id': ('django.db.models.fields.IntegerField', [], {}),
            'generic_value_ct': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'value_values'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'generic_value_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value_bool': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'value_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'value_enum': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'eav_values'", 'null': 'True', 'to': "orm['eav.EnumValue']"}),
            'value_float': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_int': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'value_page': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'eav_value'", 'unique': 'True', 'null': 'True', 'to': "orm['eav.PageLink']"}),
            'value_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'eav.weeklyschedule': {
            'Meta': {'object_name': 'WeeklySchedule'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'eav.weeklytimeblock': {
            'Meta': {'object_name': 'WeeklyTimeBlock'},
            'end_time': ('django.db.models.fields.TimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schedule': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['eav.WeeklySchedule']"}),
            'start_time': ('django.db.models.fields.TimeField', [], {}),
            'week_day': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['eav']
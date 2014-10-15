from django.db import models
from django import forms
from django.core import exceptions
import math
from south.modelsinspector import add_introspection_rules


class PositiveBigAutoField(models.AutoField):
    description = "Unsigned Big Integer"
    empty_strings_allowed = False
    MAX_BIGINT = 9223372036854775807

    def db_type(self, connection):
        if 'mysql' in connection.__class__.__module__:
            return 'bigint AUTO_INCREMENT'

        return super(PositiveBigAutoField, self).db_type(connection)


    default_error_messages = {
        'invalid': "'%(value)s' value must be an integer.",
        }

    def get_prep_value(self, value):
        if value is None:
            return None
        return int(value)

    def get_prep_lookup(self, lookup_type, value):
        if ((lookup_type == 'gte' or lookup_type == 'lt')
            and isinstance(value, float)):
            value = math.ceil(value)
        return super(PositiveBigAutoField, self).get_prep_lookup(lookup_type, value)

    def to_python(self, value):
        if value is None:
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
                )

    def formfield(self, **kwargs):
        defaults = {'min_value': 0,
                    'max_value': PositiveBigAutoField.MAX_BIGINT * 2 - 1,
                    'form_class': forms.IntegerField }
        defaults.update(kwargs)
        return super(PositiveBigAutoField, self).formfield(**defaults)

add_introspection_rules([], ["^twitter_stream\.fields\.PositiveBigAutoField"])

from django.db import models
from django import forms
from django.core import exceptions
import math

class PositiveBigIntegerField(models.BigIntegerField):
    description = "Positive Big integer"

    def get_internal_type(self):
        return "PositiveBigIntegerField"

    def formfield(self, **kwargs):
        defaults = {'min_value': 0,
                    'max_value': models.BigIntegerField.MAX_BIGINT * 2 - 1}
        defaults.update(kwargs)
        return super(PositiveBigIntegerField, self).formfield(**defaults)

    def db_type(self, connection):
        if 'mysql' in connection.__class__.__module__:
            return 'bigint UNSIGNED'
        return super(PositiveBigIntegerField, self).db_type(connection)


class PositiveBigAutoField(models.AutoField):
    description = "Unsigned Big Integer"
    empty_strings_allowed = False
    MAX_BIGINT = 9223372036854775807

    def db_type(self, connection):
        if 'mysql' in connection.__class__.__module__:
            return 'bigint UNSIGNED AUTO_INCREMENT'

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


class PositiveBigAutoForeignKey(models.ForeignKey):
    """A special foriegn key field for positive big auto fields"""

    def db_type(self, connection):
        # The database column type of a ForeignKey is the column type
        # of the field to which it points. An exception is if the ForeignKey
        # points to an AutoField/PositiveIntegerField/PositiveSmallIntegerField,
        # in which case the column type is simply that of an IntegerField.
        # If the database needs similar types for key fields however, the only
        # thing we can do is making AutoField an IntegerField.
        rel_field = self.related_field
        if isinstance(rel_field, PositiveBigAutoField):
            return PositiveBigIntegerField().db_type(connection=connection)
        return rel_field.db_type(connection=connection)
try:
    # If we are using south, we need some rules to use these fields
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^twitter_stream\.fields\.PositiveBigAutoField"])
    add_introspection_rules([], ["^twitter_stream\.fields\.PositiveBigIntegerField"])
    add_introspection_rules([], ["^twitter_stream\.fields\.PositiveBigAutoForeignKey"])
except ImportError:
    pass

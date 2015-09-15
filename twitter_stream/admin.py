from django.contrib import admin

from . import models

admin.site.register(models.FilterTerm)
admin.site.register(models.ApiKey)

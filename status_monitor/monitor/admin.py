from django.contrib import admin
from .models import Server, System

# Melhora a visualização dos Sistemas no Admin
class SystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'server')
    list_filter = ('server',)
    search_fields = ('name', 'url')

admin.site.register(Server)
admin.site.register(System, SystemAdmin)


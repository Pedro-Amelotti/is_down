from django.contrib import admin
from .models import (
    Server,
    System,
    SystemStatus,
    SystemStatusHistory,
    SystemDowntime,
)


class SystemAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "server")
    list_filter = ("server",)
    search_fields = ("name", "url")


class SystemStatusAdmin(admin.ModelAdmin):
    list_display = ("system", "status", "status_code", "checked_at")
    list_filter = ("status", "checked_at", "system__server")
    search_fields = ("system__name", "system__url")
    autocomplete_fields = ("system",)


class SystemStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("system", "status", "status_code", "checked_at")
    list_filter = ("status", "checked_at", "system__server")
    date_hierarchy = "checked_at"
    search_fields = ("system__name", "system__url")
    autocomplete_fields = ("system",)


class SystemDowntimeAdmin(admin.ModelAdmin):
    list_display = ("system", "status", "started_at", "ended_at", "duration")
    list_filter = ("status", "started_at", "ended_at", "system__server")
    date_hierarchy = "started_at"
    search_fields = ("system__name", "system__url")
    autocomplete_fields = ("system",)


admin.site.register(Server)
admin.site.register(System, SystemAdmin)
admin.site.register(SystemStatus, SystemStatusAdmin)
admin.site.register(SystemStatusHistory, SystemStatusHistoryAdmin)
admin.site.register(SystemDowntime, SystemDowntimeAdmin)


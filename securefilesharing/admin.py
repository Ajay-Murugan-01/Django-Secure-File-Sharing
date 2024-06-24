from django.contrib import admin
# import models
from .models import File

#school
class FileAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "uploaded_by", "uploaded_at")
    search_fields = ("file", "uploaded_by", "uploaded_at")
    readonly_fields = ( "uploaded_by",)


admin.site.register(File, FileAdmin)

from django.contrib import admin
from .models import Trainer, Batch, DailyClassLog

@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'subjects', 'expected_daily_hours')
    list_filter = ('subjects',)
    search_fields = ('name', 'user__username')

admin.site.register(Batch)
admin.site.register(DailyClassLog)
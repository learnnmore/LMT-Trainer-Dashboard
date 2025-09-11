from django.contrib import admin
from .models import Trainer, Batch, DailyClassLog

admin.site.register(Trainer)
admin.site.register(Batch)
admin.site.register(DailyClassLog)
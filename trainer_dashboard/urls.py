from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('trainer_app.urls')),  # Updated to trainer_app
]
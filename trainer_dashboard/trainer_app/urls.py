from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('add_trainer/', views.add_trainer, name='add_trainer'),
    path('edit_trainer/<int:trainer_id>/', views.edit_trainer, name='edit_trainer'),
    path('delete_trainer/<int:trainer_id>/', views.delete_trainer, name='delete_trainer'),
    path('add_batch/', views.add_batch, name='add_batch'),
    path('add_log/', views.add_log, name='add_log'),
    path('batch/<int:batch_id>/', views.batch_details, name='batch_details'),
    path('weekly_report/', views.weekly_report, name='weekly_report'),
]
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('add_trainer/', views.add_trainer, name='add_trainer'),
    path('edit_trainer/<int:trainer_id>/', views.edit_trainer, name='edit_trainer'),
    path('delete_trainer/<int:trainer_id>/', views.delete_trainer, name='delete_trainer'),
    path('add_batch/', views.add_batch, name='add_batch'),
    path('add_log/', views.add_log, name='add_log'),
    path('batch/<int:batch_id>/', views.batch_details, name='batch_details'),
    path('weekly_report/', views.weekly_report, name='weekly_report'),
     path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
     path("after_login/", views.after_login, name="after_login"),
     path("add-trainer-admin/", views.add_trainer_admin, name="add_trainer_admin"),

]
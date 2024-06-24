from django.urls import path

# import views
from . import views
from .views import *

from django.urls import path

# import views
from . import views

urlpatterns = [

    path('signup', views.SignUpView().as_view(), name='signup'),
    path('login/', views.Loginview().as_view(), name='login'),
    path('upload-file', views.UploadFileView().as_view(), name='upload-file'),
    path('uploaded-file', views.ClientUserListFilesView().as_view(), name='uploaded-file'),
    path('download-file/<int:pk>/', DownloadFileView.as_view(), name='download_file'),
    path('serve_protected_file/', serve_protected_file, name='serve_protected_file'),

]
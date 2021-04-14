"""notekeeper URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.urls import include
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('notes/delete/attach/<int:fk>/', login_required(views.delete_file), name='delete_file'),
    path('notes/<int:pk>/delete/confirm/<int:fk>/attach', login_required(views.confirm_delete_file), name='confirm_delete_file'),
    path('notes/<int:pk>/edit/attach', login_required(views.edit_note_files), name='edit_note_files'),
]

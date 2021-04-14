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
    path('notes/', login_required(views.home), name='notes'),       # for adding a new book
    path('notes/search/', views.search_note, name='search_note'),
    path('notes/<slug:slug>/', views.get_note_details, name='note_detail'),
    path('notes/<int:pk>/delete/', login_required(views.delete_note), name='delete_note'),
    path('notes/<int:pk>/delete/confirm/', login_required(views.confirm_delete_note), name='confirm_delete_note'),
    path('notes/<int:pk>/edit/', login_required(views.edit_note_details), name='note_details_edit'),
    path('notes/<slug:slug>/pdf/', login_required(views.generate_pdf), name='note_as_pdf'),
    path('notes/<slug:slug>/zip/', views.generate_zip, name='note_as_zip'),
    path('project/<str:proj>/timeline/zip/', login_required(views.generate_timeline_zip), name='timeline_as_zip'),
    path('notes/share/<str:signed_pk>/', login_required(views.get_shareable_link), name='share_notes'),
    path('tags/<slug:slug>/', login_required(views.get_all_notes_tags), name='get_all_notes_tags'),
    path('project/<str:proj>/timeline', login_required(views.get_timeline_proj), name='get_timeline_proj'),
    path('project/<str:proj>', login_required(views.get_proj), name='get_proj'),
    path('projects/', views.projects, name='get_all_proj'),
    path('public/', views.public_projects, name='public'),
    path('shared/', login_required(views.shared), name='get_all_shared'),
    path('', views.home, name='home'),
    path('accounts/delete/confirm/', login_required(views.confirm_delete_account), name='confirm_delete_account'),
    path('accounts/delete/<str:username>', login_required(views.delete_account), name='delete_account'),
]

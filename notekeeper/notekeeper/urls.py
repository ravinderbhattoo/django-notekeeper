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
from django.contrib import admin
from django.urls import path
from django.urls import include
from accounts import views
from django.contrib.auth.views import LoginView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/create_default_accounts/', views.create_default_accounts, name='create_default_accounts'),
    path('accounts/login/', LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/change_password/', views.change_password, name='change_password'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('', include('notes.urls')),
    path('', include('attachments.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

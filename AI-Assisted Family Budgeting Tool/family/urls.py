"""
URL configuration for family_budget project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from app import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('first',views.first,name="first"),
    path('home',views.home,name='home'),
    path('month_history',views.month_history,name='month_history'),
    path('',views.login_view,name="login"),
    path('register',views.register,name="register"),
    path('logout',views.logout_view,name="logout"),
    path('delete/<int:expense_id>/', views.delete_expense, name='delete'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

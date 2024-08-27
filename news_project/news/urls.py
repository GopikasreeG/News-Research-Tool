# news_project/urls.py
from django.contrib import admin
from django.urls import path
from news import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signin/', views.signup_view, name='signin'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('news/', views.news_list, name='news_list'),  # Ensure this line exists
    path('', views.index, name='index'),
]

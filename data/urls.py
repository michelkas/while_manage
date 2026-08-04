from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('articles/ajouter/', views.create_article, name='create_article'),
    path('stock/ajouter/', views.create_stock_entry, name='create_stock_entry'),
    path('ventes/ajouter/', views.create_income, name='create_income'),
    path('depenses/ajouter/', views.create_expense, name='create_expense'),
]

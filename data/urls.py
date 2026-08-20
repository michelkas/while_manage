from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('articles/ajouter/', views.create_article, name='create_article'),
    path('stock/ajouter/', views.create_stock_entry, name='create_stock_entry'),
    path('ventes/ajouter/', views.create_income, name='create_income'),
    path('depenses/ajouter/', views.create_expense, name='create_expense'),
    path('articles/<uuid:article_id>/modifier/', views.update_article, name='update_article'),
    path('articles/<uuid:article_id>/supprimer/', views.delete_article, name='delete_article'),
    path('ventes/<uuid:income_id>/modifier/', views.update_income, name='update_income'),
    path('ventes/<uuid:income_id>/supprimer/', views.delete_income, name='delete_income'),
    path('depenses/<uuid:expense_id>/modifier/', views.update_expense, name='update_expense'),
    path('depenses/<uuid:expense_id>/supprimer/', views.delete_expense, name='delete_expense'),
]

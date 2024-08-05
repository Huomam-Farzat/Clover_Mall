from django.urls import path
from . import views

urlpatterns = [
    path('inputdata/', views.inputData, name='inputdata'),
    path('getuser/', views.getuser, name='getuser'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('test/', views.test_token, name='test_token'),
    path('logout/', views.logout, name='logout'),
    
    path('product/', views.get_products, name='get_products'),
    
    
    path('products/category/<str:category_name>/', views.get_products_by_category, name='get_products_by_category'),
    path('products/add/', views.enter_product, name='enter_product'),
    
    
    
    
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/', views.get_orders, name='get_orders'),
    path('orders/user/', views.get_user_orders, name='get_user_orders'),
    path('orders/main-categories/', views.get_orders_by_main_categories, name='get_orders_by_main_categories'),
    path('orders/store/<str:store_name>/', views.get_orders_by_store, name='get_orders_by_store'),


    path('product/newProducts' , views.newproducts , name='newProducts'),
    path('product/bestrate' , views.bestrate , name='bestrate' ),
    path('product/rateplus' , views.rateplus , name='rateplus' ),
    path('product/rateminus' , views.rateminus , name='rateminus' )
]

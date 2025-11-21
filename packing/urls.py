from django.urls import path
from .views import *


app_name = 'packing'
urlpatterns = [
    path('', packingHomeList.as_view(), name='packing-home'),
    path('ajout-packing/', ajoutPacking.as_view(), name='ajout-packing'),
    path('ajout-packing-panne/<slug:slug>/', ajoutPanne.as_view(), name='ajout-packing-panne'),
    path('user-packing-detail/<str:username>/', userPackingDetail.as_view(), name='user-packing-detail'),
    path('user-packing-panne-detail/<str:username>/', userPackingPanneDetail.as_view(), name='user-packing-panne-detail'),
    path('packing-update/<slug:slug>/', updatePacking.as_view(), name='packing-update'),
    path('packing-delete/<slug:slug>', deletePacking.as_view(), name='packing-delete'),
    path('modifier-panne/<slug:slug>/', updatePackingPanne.as_view(), name='modifier-panne'),
    path('packing-panne-delete/<slug:slug>/', deletePackingPanne.as_view(), name='packing-panne-delete'),
    path('admin-packing/', adminPackingView.as_view(), name='admin-packing'),
    path('admin-packing-panne/', adminPackingPanneViews.as_view(), name='admin-packing-panne'),
    path('packing/<str:username>/pdf/', userPackingPanneDetailPdf.as_view(), name='user_packing_panne_pdf'),
    
    path('dashboard-packing/', dashboard.as_view(), name='dashboard_packing'),
]

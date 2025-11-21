from django.urls import path
from.views import *

app_name = 'broyage'
urlpatterns = [
    path('', broyageHomeList.as_view(), name='broyage-home'),
    path('ajout-totaliseur/', ajouTotali.as_view(), name='ajout-totalisuer'),
    path('ajout-broyage/<slug:slug>/', ajoutBroyage.as_view(), name='ajout-broyage'),
    path('ajout-broyage-panne/<slug:slug>/', ajoutPanne.as_view(), name='ajout-broyage-panne'),
    path('update-totalisuer/ <slug:slug>/', updateTotali.as_view(), name='update-totaliseur'),
    path('update-broyage/ <slug:slug>/', updateBroyage.as_view(), name='update-broyage'),
    path('modifier-panne/<slug:slug>/', updatePanne.as_view(), name='modifier-panne'),
    
    path('broyage-user-view/<str:username>/', broyageUserView.as_view(), name='broyage-user-view'),
    path('broyage-panne-user-view/<str:username>/', broyeurPanneUserView.as_view(), name='broyage-panne-user-view'),
    
    path('admin-broyage-view/', adminBroyage.as_view(), name='admin-broyage'),
    path('admin-broyage_panne-view/', adminBroyagePanne.as_view(), name='admin-broyage-panne'),
    
    path('dashboard-broyage/', dashboard.as_view(), name='dashboard_broyage'),
]

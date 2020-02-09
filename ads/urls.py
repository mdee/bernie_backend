from django.urls import path

from . import views

urlpatterns = [
    path('ads/', views.AdList.as_view({'get': 'list'})),
    path('campaigns/', views.PresidentialCampaignList.as_view({'get': 'list'})),
    path('date_extent/', views.DateExtentList.as_view({'get': 'list'})),
    path('date_ads_metadata/', views.DateRangeAdMetaList.as_view({'get': 'list'})),
    path('date_donations_metadata/', views.DateDonationMetaList.as_view({'get': 'list'})),

]

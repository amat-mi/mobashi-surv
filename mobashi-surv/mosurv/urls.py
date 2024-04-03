# Django Rest Framework url
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampaignViewSet, SchoolViewSet, CaschoViewSet, SurveyViewSet, HarvestViewSet

router = DefaultRouter()
router.register(r'schools', SchoolViewSet, basename="school")
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'caschos', CaschoViewSet, basename='cascho')
router.register(r'surveys', SurveyViewSet, basename='survey')
router.register(r'harvests', HarvestViewSet, basename='harvest')

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import	path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, EmployerViewSet, SeekerViewSet, JobViewSet,
    ApplicationViewSet, FavoriteViewSet, ChatViewSet, MessageViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'employers', EmployerViewSet)
router.register(r'seekers', SeekerViewSet)
router.register(r'jobs', JobViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'favorites', FavoriteViewSet)
router.register(r'chats', ChatViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

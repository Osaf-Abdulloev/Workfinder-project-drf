from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    CategoryViewSet, EmployerViewSet, SeekerViewSet, JobViewSet,
    ApplicationViewSet, FavoriteViewSet, ChatViewSet, MessageViewSet,
    register, create_seeker_profile, create_employer_profile, logout,
    notification_list, mark_all_read, delete_notification,
    analyze_resume, match_jobs, admin_stats, report_user
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
    path('auth/register/', register),
    path('auth/login/', TokenObtainPairView.as_view()),
    path('auth/logout/', logout),
    path('auth/token/refresh/', TokenRefreshView.as_view()),
    path('create-seeker-profile/', create_seeker_profile),
    path('create-employer-profile/', create_employer_profile),
    path('notifications/', notification_list),
    path('notifications/read-all/', mark_all_read),
    path('notifications/<int:pk>/delete/', delete_notification),
    path('analyze-resume/', analyze_resume),
    path('match-jobs/', match_jobs),
    path('admin-stats/', admin_stats),
    path('report-user/', report_user),
]
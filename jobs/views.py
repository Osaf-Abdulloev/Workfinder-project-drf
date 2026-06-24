from rest_framework import viewsets
from .models import Employer, Seeker, Category, Job, Application, Favorite, Chat, Message
from .serializers import (
    EmployerSerializer, SeekerSerializer, CategorySerializer, JobSerializer,
    ApplicationSerializer, FavoriteSerializer, ChatSerializer, MessageSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class EmployerViewSet(viewsets.ModelViewSet):
    queryset = Employer.objects.all()
    serializer_class = EmployerSerializer


class SeekerViewSet(viewsets.ModelViewSet):
    queryset = Seeker.objects.all()
    serializer_class = SeekerSerializer


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

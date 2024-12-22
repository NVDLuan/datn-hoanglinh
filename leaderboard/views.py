from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from leaderboard.models import Leaderboard
from leaderboard.serializers import LeaderboardSerializer


# Create your views here.
class LeaderboardViewSet(ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer
    permission_classes = [IsAuthenticated]
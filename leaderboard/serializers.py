from rest_framework import serializers

from leaderboard.models import Leaderboard


class LeaderboardSerializer(serializers.ModelSerializer):

    class Meta:
        model = Leaderboard
        fields = '__all__'
        ordering = ['-score']
from rest_framework import serializers

from question.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="answer_text")

    class Meta:
        model = Question
        fields = ['image', 'name']

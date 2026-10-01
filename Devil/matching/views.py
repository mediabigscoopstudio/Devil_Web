from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from .models import Match
from .serializers import MatchSerializer

class MatchListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        matches = Match.objects.filter(
            Q(user_one=request.user) | Q(user_two=request.user),
            is_active=True
        ).order_by('-matched_at')
        return Response(MatchSerializer(matches, many=True, context={'request': request}).data)

class MatchDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            match = Match.objects.get(
                Q(user_one=request.user) | Q(user_two=request.user),
                id=pk,
                is_active=True
            )
            return Response(MatchSerializer(match, context={'request': request}).data)
        except Match.DoesNotExist:
            return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            match = Match.objects.get(
                Q(user_one=request.user) | Q(user_two=request.user),
                id=pk
            )
            match.is_active = False
            match.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Match.DoesNotExist:
            return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)

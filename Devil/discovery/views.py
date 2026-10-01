from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from profiles.models import Profile
from discovery.models import Swipe
from matching.models import Match
from messaging.models import Conversation
from moderation.models import Block
from accounts.models import User
from .serializers import DiscoveryProfileSerializer

class DiscoveryFeedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        current_user = request.user
        
        # Exclude self, blocked users, users who blocked me, already swiped users
        blocked_by_me = Block.objects.filter(blocker=current_user).values_list('blocked_id', flat=True)
        blocked_me = Block.objects.filter(blocked=current_user).values_list('blocker_id', flat=True)
        swiped_user_ids = Swipe.objects.filter(from_user=current_user).values_list('to_user_id', flat=True)

        exclude_ids = set(list(blocked_by_me) + list(blocked_me) + list(swiped_user_ids) + [current_user.id])

        candidates = Profile.objects.filter(
            user__status='ACTIVE',
            is_discoverable=True
        ).exclude(user_id__in=exclude_ids)[:20]

        return Response(DiscoveryProfileSerializer(candidates, many=True).data)

class SwipeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        target_user_id = request.data.get('target_user_id')
        action = request.data.get('action') # LIKE, PASS, SPECIAL_LIKE

        if not target_user_id or action not in ['LIKE', 'PASS', 'SPECIAL_LIKE']:
            return Response({'error': 'target_user_id and valid action are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({'error': 'Target user not found'}, status=status.HTTP_404_NOT_FOUND)

        swipe, _ = Swipe.objects.get_or_create(
            from_user=request.user,
            to_user=target_user,
            defaults={'action': action}
        )

        matched = False
        match_id = None

        if action in ['LIKE', 'SPECIAL_LIKE']:
            # Check for reciprocal swipe
            reciprocal = Swipe.objects.filter(
                from_user=target_user,
                to_user=request.user,
                action__in=['LIKE', 'SPECIAL_LIKE']
            ).first()

            if reciprocal:
                matched = True
                u1, u2 = (request.user, target_user) if request.user.id < target_user.id else (target_user, request.user)
                match, created = Match.objects.get_or_create(user_one=u1, user_two=u2)
                match_id = str(match.id)
                if created:
                    Conversation.objects.create(match=match)

        return Response({
            'action': action,
            'matched': matched,
            'match_id': match_id
        })

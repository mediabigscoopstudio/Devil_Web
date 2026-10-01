import os

base_dir = '/Volumes/Juggernut_Assist/Projects/Devil/Devil_web/Devil'

# 1. PROFILES SERIALIZERS & VIEWS
profiles_serializers = '''from rest_framework import serializers
from .models import Profile, ProfilePhoto, Interest, Preference, ProfileInterest

class ProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePhoto
        fields = ['id', 'image', 'sort_order', 'is_primary', 'created_at']

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ['minimum_age', 'maximum_age', 'maximum_distance_km', 'preferred_genders']

class ProfileSerializer(serializers.ModelSerializer):
    photos = ProfilePhotoSerializer(many=True, read_only=True)
    interests = serializers.SerializerMethodField()
    preference = PreferenceSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'display_name', 'date_of_birth', 'gender', 'bio',
            'location_latitude', 'location_longitude', 'location_name',
            'is_discoverable', 'profile_completed', 'photos', 'interests', 'preference'
        ]

    def get_interests(self, obj):
        interests = Interest.objects.filter(profileinterest__profile=obj)
        return InterestSerializer(interests, many=True).data
'''

profiles_views = '''from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Profile, ProfilePhoto, Interest, Preference, ProfileInterest
from .serializers import ProfileSerializer, ProfilePhotoSerializer, InterestSerializer, PreferenceSerializer

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save(profile_completed=True)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PhotoListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        photos = ProfilePhoto.objects.filter(profile=profile).order_by('sort_order')
        return Response(ProfilePhotoSerializer(photos, many=True).data)

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'Image file is required'}, status=status.HTTP_400_BAD_REQUEST)
        is_primary = not ProfilePhoto.objects.filter(profile=profile, is_primary=True).exists()
        photo = ProfilePhoto.objects.create(profile=profile, image=image, is_primary=is_primary)
        return Response(ProfilePhotoSerializer(photo).data, status=status.HTTP_201_CREATED)

class PhotoDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            photo = ProfilePhoto.objects.get(id=pk, profile__user=request.user)
            photo.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProfilePhoto.DoesNotExist:
            return Response({'error': 'Photo not found'}, status=status.HTTP_404_NOT_FOUND)

class InterestListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        interests = Interest.objects.all()
        return Response(InterestSerializer(interests, many=True).data)

class UserInterestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        interest_ids = request.data.get('interest_ids', [])
        ProfileInterest.objects.filter(profile=profile).delete()
        for i_id in interest_ids:
            try:
                interest = Interest.objects.get(id=i_id)
                ProfileInterest.objects.create(profile=profile, interest=interest)
            except Interest.DoesNotExist:
                pass
        return Response({'message': 'Interests updated successfully'})

class PreferenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        pref, _ = Preference.objects.get_or_create(profile=profile)
        return Response(PreferenceSerializer(pref).data)

    def put(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        pref, _ = Preference.objects.get_or_create(profile=profile)
        serializer = PreferenceSerializer(pref, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
'''

profiles_urls = '''from django.urls import path
from .views import ProfileView, PhotoListCreateView, PhotoDetailView, InterestListView, UserInterestView, PreferenceView

urlpatterns = [
    path('', ProfileView.as_view(), name='profile'),
    path('photos/', PhotoListCreateView.as_view(), name='photo-list-create'),
    path('photos/<uuid:pk>/', PhotoDetailView.as_view(), name='photo-detail'),
    path('interests/all/', InterestListView.as_view(), name='interest-list'),
    path('interests/', UserInterestView.as_view(), name='user-interests'),
    path('preferences/', PreferenceView.as_view(), name='preferences'),
]
'''

# 2. DISCOVERY SERIALIZERS & VIEWS
discovery_serializers = '''from rest_framework import serializers
from profiles.models import Profile, ProfilePhoto
from profiles.serializers import ProfilePhotoSerializer, InterestSerializer

class DiscoveryProfileSerializer(serializers.ModelSerializer):
    photos = ProfilePhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'display_name', 'gender', 'bio', 'photos', 'location_name']
'''

discovery_views = '''from rest_framework.views import APIView
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
'''

discovery_urls = '''from django.urls import path
from .views import DiscoveryFeedView, SwipeView

urlpatterns = [
    path('', DiscoveryFeedView.as_view(), name='discovery-feed'),
    path('swipe/', SwipeView.as_view(), name='swipe'),
]
'''

# 3. MATCHING SERIALIZERS & VIEWS
matching_serializers = '''from rest_framework import serializers
from .models import Match
from profiles.serializers import ProfileSerializer

class MatchSerializer(serializers.ModelSerializer):
    other_user_profile = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = ['id', 'matched_at', 'is_active', 'other_user_profile']

    def get_other_user_profile(self, obj):
        request_user = self.context.get('request').user
        other_user = obj.user_two if obj.user_one == request_user else obj.user_one
        if hasattr(other_user, 'profile'):
            return ProfileSerializer(other_user.profile).data
        return None
'''

matching_views = '''from rest_framework.views import APIView
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
'''

matching_urls = '''from django.urls import path
from .views import MatchListView, MatchDetailView

urlpatterns = [
    path('', MatchListView.as_view(), name='match-list'),
    path('<uuid:pk>/', MatchDetailView.as_view(), name='match-detail'),
]
'''

# 4. MESSAGING SERIALIZERS & VIEWS
messaging_serializers = '''from rest_framework import serializers
from .models import Conversation, Message
from matching.serializers import MatchSerializer

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'message_type', 'text', 'is_read', 'created_at']
        read_only_fields = ['sender', 'conversation']

class ConversationSerializer(serializers.ModelSerializer):
    match = MatchSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'match', 'is_active', 'created_at', 'last_message']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
'''

messaging_views = '''from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

class ConversationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(
            Q(match__user_one=request.user) | Q(match__user_two=request.user),
            is_active=True
        ).order_by('-updated_at')
        return Response(ConversationSerializer(conversations, many=True, context={'request': request}).data)

class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            conversation = Conversation.objects.get(
                Q(match__user_one=request.user) | Q(match__user_two=request.user),
                id=pk,
                is_active=True
            )
            return Response(ConversationSerializer(conversation, context={'request': request}).data)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

class MessageListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                Q(match__user_one=request.user) | Q(match__user_two=request.user),
                id=conversation_id
            )
            messages = conversation.messages.order_by('created_at')
            return Response(MessageSerializer(messages, many=True).data)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                Q(match__user_one=request.user) | Q(match__user_two=request.user),
                id=conversation_id,
                is_active=True
            )
            text = request.data.get('text')
            if not text:
                return Response({'error': 'Message text is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                text=text
            )
            conversation.save() # updates updated_at
            return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

class MarkMessageReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            msg = Message.objects.get(id=pk)
            if msg.conversation.match.user_one == request.user or msg.conversation.match.user_two == request.user:
                msg.is_read = True
                msg.save()
                return Response({'status': 'marked as read'})
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
'''

messaging_urls = '''from django.urls import path
from .views import ConversationListView, ConversationDetailView, MessageListCreateView, MarkMessageReadView

urlpatterns = [
    path('', ConversationListView.as_view(), name='conversation-list'),
    path('<uuid:pk>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('<uuid:conversation_id>/messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<uuid:pk>/read/', MarkMessageReadView.as_view(), name='message-read'),
]
'''

# Write files
files_to_write = {
    'profiles/serializers.py': profiles_serializers,
    'profiles/views.py': profiles_views,
    'profiles/urls.py': profiles_urls,
    
    'discovery/serializers.py': discovery_serializers,
    'discovery/views.py': discovery_views,
    'discovery/urls.py': discovery_urls,
    
    'matching/serializers.py': matching_serializers,
    'matching/views.py': matching_views,
    'matching/urls.py': matching_urls,
    
    'messaging/serializers.py': messaging_serializers,
    'messaging/views.py': messaging_views,
    'messaging/urls.py': messaging_urls,
}

for rel_path, content in files_to_write.items():
    full_path = os.path.join(base_dir, rel_path)
    with open(full_path, 'w') as f:
        f.write(content)

# Update main urls.py to include all endpoints
main_urls = '''from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/profile/', include('profiles.urls')),
    path('api/v1/discovery/', include('discovery.urls')),
    path('api/v1/matches/', include('matching.urls')),
    path('api/v1/conversations/', include('messaging.urls')),
]
'''

with open(os.path.join(base_dir, 'Devil', 'urls.py'), 'w') as f:
    f.write(main_urls)

print("Stage 2 APIs (Profiles, Discovery, Matching, Messaging) scaffolded successfully.")

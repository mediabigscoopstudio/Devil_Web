from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db import transaction
from .models import Profile, ProfilePhoto, Interest, DatingIntent
from .serializers import (
    ProfileSerializer, ProfileUpdateSerializer, LocationUpdateSerializer,
    NotificationPreferenceSerializer, ProfilePhotoSerializer
)

class ProfileMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response({
            'success': True,
            'profile': serializer.data
        })

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            dob = serializer.validated_data.get('date_of_birth', profile.date_of_birth)
            if dob:
                today = timezone.localdate()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                if age < 18:
                    return Response({
                        "success": False,
                        "error": {
                            "code": "AGE_RESTRICTED",
                            "message": "You must be 18 or older to use Devil."
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Handle M2M relationships manually since they are write-only fields
            looking_for_codes = serializer.validated_data.pop('looking_for', None)
            interest_ids = serializer.validated_data.pop('interests', None)
            
            with transaction.atomic():
                profile = serializer.save()
                
                if looking_for_codes is not None:
                    intents = DatingIntent.objects.filter(code__in=looking_for_codes)
                    profile.looking_for.set(intents)
                    
                if interest_ids is not None:
                    interests = Interest.objects.filter(id__in=interest_ids)
                    profile.interests.set(interests)
            
            # Re-fetch profile to serialize it
            return Response({
                'success': True,
                'profile': ProfileSerializer(profile).data
            })
            
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid data provided.',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

class ProfileLocationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = LocationUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(location_updated_at=timezone.now())
            return Response({'success': True, 'profile': ProfileSerializer(profile).data})
        return Response({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'details': serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

class ProfileNotificationPreferenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'profile': ProfileSerializer(profile).data})
        return Response({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'details': serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)

class ProfileCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        
        errors = {}
        if not profile.display_name:
            errors['display_name'] = "Display name is required."
        if not profile.date_of_birth:
            errors['date_of_birth'] = "Date of birth is required."
        if not profile.gender:
            errors['gender'] = "Gender is required."
        if profile.looking_for.count() == 0:
            errors['looking_for'] = "Select at least one dating intent."
        if profile.interests.count() < 3:
            errors['interests'] = "Select at least 3 interests."
        if profile.photos.count() < 3:
            errors['photos'] = "Add at least 3 photos."
            
        if errors:
            return Response({
                "success": False,
                "error": {
                    "code": "PROFILE_INCOMPLETE",
                    "message": "Please complete the required profile fields.",
                    "fields": errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            profile.profile_completed = True
            profile.save(update_fields=['profile_completed'])
            
        return Response({
            "success": True,
            "profile_completed": True,
            "requires_onboarding": False
        })

class PhotoListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        photos = profile.photos.all().order_by('sort_order')
        return Response({
            'success': True,
            'photos': ProfilePhotoSerializer(photos, many=True).data
        })

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        
        if profile.photos.count() >= 6:
            return Response({
                "success": False,
                "error": {
                    "code": "PHOTO_LIMIT_EXCEEDED",
                    "message": "You can only upload a maximum of 6 photos."
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if 'image' not in request.FILES:
            return Response({'success': False, 'error': {'code': 'INVALID_REQUEST', 'message': 'No image provided.'}}, status=status.HTTP_400_BAD_REQUEST)
            
        is_primary = profile.photos.count() == 0
        sort_order = profile.photos.count()
        
        photo = ProfilePhoto.objects.create(
            profile=profile,
            image=request.FILES['image'],
            is_primary=is_primary,
            sort_order=sort_order
        )
        
        return Response({
            'success': True,
            'photo': ProfilePhotoSerializer(photo).data
        })

class PhotoDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        try:
            photo = profile.photos.get(pk=pk)
        except ProfilePhoto.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        if 'is_primary' in request.data and request.data['is_primary']:
            with transaction.atomic():
                profile.photos.all().update(is_primary=False)
                photo.is_primary = True
                photo.save(update_fields=['is_primary'])
                
        if 'sort_order' in request.data:
            photo.sort_order = int(request.data['sort_order'])
            photo.save(update_fields=['sort_order'])
            
        return Response({'success': True, 'photo': ProfilePhotoSerializer(photo).data})

    def delete(self, request, pk):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        try:
            photo = profile.photos.get(pk=pk)
        except ProfilePhoto.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        if profile.photos.count() == 1:
            return Response({
                "success": False,
                "error": {
                    "code": "MIN_PHOTO_ERROR",
                    "message": "Cannot delete the last remaining photo."
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
        was_primary = photo.is_primary
        photo.delete()
        
        if was_primary:
            first = profile.photos.order_by('sort_order').first()
            if first:
                first.is_primary = True
                first.save(update_fields=['is_primary'])
                
        return Response({'success': True})

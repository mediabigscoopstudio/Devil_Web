from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from .models import Profile, ProfilePhoto, Interest, DatingIntent
from .serializers import (
    ProfileSerializer, ProfileUpdateSerializer, LocationUpdateSerializer,
    NotificationPreferenceSerializer, ProfilePhotoSerializer, InterestSerializer, DatingIntentSerializer
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
            # Handle M2M relationships safely
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
            
            return Response({
                'success': True,
                'profile': ProfileSerializer(profile).data
            })
            
        # Format errors safely
        error_dict = list(serializer.errors.values())[0][0] if serializer.errors else {}
        if isinstance(error_dict, dict) and 'code' in error_dict:
            return Response({
                'success': False,
                'error': error_dict
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid data provided.',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

class InterestListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        interests = Interest.objects.filter(is_active=True).order_by('sort_order', 'name')
        return Response({
            'success': True,
            'interests': InterestSerializer(interests, many=True).data
        })

class DatingIntentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        intents = DatingIntent.objects.filter(is_active=True).order_by('sort_order')
        return Response({
            'success': True,
            'dating_intents': DatingIntentSerializer(intents, many=True).data
        })

class ProfileLocationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = LocationUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(location_updated_at=timezone.now())
            return Response({'success': True, 'profile': ProfileSerializer(profile).data})
            
        error_dict = list(serializer.errors.values())[0][0] if serializer.errors else {}
        if isinstance(error_dict, dict) and 'code' in error_dict:
            return Response({'success': False, 'error': error_dict}, status=status.HTTP_400_BAD_REQUEST)
            
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
        
        if profile.profile_completed:
            return Response({
                "success": True,
                "profile_completed": True,
                "requires_onboarding": False
            })
            
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
            
        serializer = ProfilePhotoSerializer(data=request.data)
        if serializer.is_valid():
            is_primary = profile.photos.count() == 0
            sort_order = profile.photos.count()
            
            with transaction.atomic():
                photo = serializer.save(
                    profile=profile,
                    is_primary=is_primary,
                    sort_order=sort_order
                )
            return Response({'success': True, 'photo': ProfilePhotoSerializer(photo).data})
            
        error_dict = list(serializer.errors.values())[0][0] if serializer.errors else {}
        if isinstance(error_dict, dict) and 'code' in error_dict:
            return Response({'success': False, 'error': error_dict}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({'success': False, 'error': {'code': 'INVALID_REQUEST', 'message': 'Invalid image'}}, status=status.HTTP_400_BAD_REQUEST)


class PhotoDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        try:
            photo = profile.photos.get(pk=pk)
        except ProfilePhoto.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        with transaction.atomic():
            if 'is_primary' in request.data and request.data['is_primary'] is True:
                profile.photos.all().update(is_primary=False)
                photo.is_primary = True
                photo.save(update_fields=['is_primary'])
                
            if 'sort_order' in request.data:
                new_order = int(request.data['sort_order'])
                old_order = photo.sort_order
                photo_count = profile.photos.count()
                
                if new_order < 0 or new_order >= photo_count:
                    return Response({
                        "success": False,
                        "error": {
                            "code": "INVALID_SORT_ORDER",
                            "message": f"Sort order must be between 0 and {photo_count - 1}."
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if new_order != old_order:
                    # Deterministic shift
                    if new_order < old_order:
                        profile.photos.filter(sort_order__gte=new_order, sort_order__lt=old_order).update(sort_order=F('sort_order') + 1)
                    else:
                        profile.photos.filter(sort_order__gt=old_order, sort_order__lte=new_order).update(sort_order=F('sort_order') - 1)
                    photo.sort_order = new_order
                    photo.save(update_fields=['sort_order'])
                    
                    # Ensure 0 to N normalization safely
                    all_photos = list(profile.photos.order_by('sort_order'))
                    for i, p in enumerate(all_photos):
                        if p.sort_order != i:
                            p.sort_order = i
                            p.save(update_fields=['sort_order'])
            
        photo.refresh_from_db()
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
            
        with transaction.atomic():
            was_primary = photo.is_primary
            photo.delete()
            
            # Reorder
            all_photos = list(profile.photos.order_by('sort_order'))
            for i, p in enumerate(all_photos):
                if p.sort_order != i:
                    p.sort_order = i
                    p.save(update_fields=['sort_order'])
            
            # Reassign primary
            if was_primary and all_photos:
                first = all_photos[0]
                first.is_primary = True
                first.save(update_fields=['is_primary'])
                
        return Response({'success': True})

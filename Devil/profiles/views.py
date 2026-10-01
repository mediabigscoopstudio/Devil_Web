from rest_framework.views import APIView
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

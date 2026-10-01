from rest_framework import serializers
from profiles.models import Profile, ProfilePhoto
from profiles.serializers import ProfilePhotoSerializer, InterestSerializer

class DiscoveryProfileSerializer(serializers.ModelSerializer):
    photos = ProfilePhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'display_name', 'gender', 'bio', 'photos', 'location_name']

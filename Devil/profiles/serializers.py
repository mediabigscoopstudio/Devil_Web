from rest_framework import serializers
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

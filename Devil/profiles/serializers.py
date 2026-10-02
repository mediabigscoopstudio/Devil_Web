import io
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from .models import Profile, ProfilePhoto, Interest, Preference, DatingIntent

def validate_age_rule(date_of_birth):
    if not date_of_birth:
        return
    today = timezone.localdate()
    if date_of_birth > today:
        raise ValidationError({"code": "INVALID_DATE_OF_BIRTH", "message": "Date of birth cannot be in the future."})
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    if age < 18:
        raise ValidationError({"code": "AGE_RESTRICTED", "message": "You must be 18 or older to use Devil."})

class DatingIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatingIntent
        fields = ['code', 'label']

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name', 'slug']

class ProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePhoto
        fields = ['id', 'image', 'sort_order', 'is_primary']

    def validate_image(self, value):
        # File size check
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise ValidationError({"code": "IMAGE_TOO_LARGE", "message": "Image must be smaller than 10 MB."})

        # Format and dimensions check
        try:
            # We need to read the image data to open it with PIL
            value.seek(0)
            img = Image.open(io.BytesIO(value.read()))
            img.verify()
        except UnidentifiedImageError:
            raise ValidationError({"code": "INVALID_IMAGE", "message": "The uploaded file is not a valid image."})
        except (IOError, SyntaxError):
            raise ValidationError({"code": "INVALID_IMAGE", "message": "The uploaded image file is corrupted."})
            
        value.seek(0)
        img = Image.open(io.BytesIO(value.read()))
        format = img.format
        allowed_formats = ['JPEG', 'PNG', 'WEBP']
        if format not in allowed_formats:
            raise ValidationError({"code": "INVALID_IMAGE", "message": "The uploaded file is not a valid image format."})
            
        width, height = img.size
        if width < 300 or height < 300:
            raise ValidationError({"code": "INVALID_IMAGE", "message": "Image must be at least 300x300 pixels."})
        if width > 8000 or height > 8000:
            raise ValidationError({"code": "INVALID_IMAGE", "message": "Image dimensions are too large."})

        # Reset file pointer after reading
        value.seek(0)
        return value

class ProfileSerializer(serializers.ModelSerializer):
    photos = ProfilePhotoSerializer(many=True, read_only=True)
    interests = InterestSerializer(many=True, read_only=True)
    looking_for = DatingIntentSerializer(many=True, read_only=True)
    age = serializers.IntegerField(read_only=True)
    gender = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'display_name', 'age', 'date_of_birth', 'gender', 'looking_for', 'interests', 
            'photos', 'bio', 'city', 'country', 'location_enabled', 'profile_completed',
            'notifications_enabled', 'notifications_permission_status', 'distance_km'
        ]
        
    def get_gender(self, obj):
        if not obj.gender:
            return None
        return {
            'code': obj.gender,
            'label': dict(Profile.GENDER_CHOICES).get(obj.gender, obj.gender)
        }
        
    def get_distance_km(self, obj):
        # We don't expose exact lat/long here. For now, returning None. 
        # Discovery logic would calculate this relative to the requesting user.
        return None

class ProfileUpdateSerializer(serializers.ModelSerializer):
    looking_for = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True
    )
    interests = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    
    class Meta:
        model = Profile
        fields = [
            'display_name', 'date_of_birth', 'gender', 'bio', 
            'looking_for', 'interests'
        ]

    def validate_bio(self, value):
        if len(value) > 300:
            raise ValidationError({"code": "BIO_TOO_LONG", "message": "Bio must be 300 characters or less."})
        return value

    def validate_date_of_birth(self, value):
        validate_age_rule(value)
        return value

    def validate_looking_for(self, value):
        if value is None:
            return value
        valid_intents = DatingIntent.objects.filter(code__in=value, is_active=True).values_list('code', flat=True)
        if len(valid_intents) != len(set(value)):
            raise ValidationError({"code": "INVALID_DATING_INTENTS", "message": "One or more selected dating intents are invalid."})
        return value

    def validate_interests(self, value):
        if value is None:
            return value
        valid_interests = Interest.objects.filter(id__in=value, is_active=True).values_list('id', flat=True)
        if len(valid_interests) != len(set(value)):
            raise ValidationError({"code": "INVALID_INTERESTS", "message": "One or more selected interests are invalid."})
            
        if len(value) > 10:
            raise ValidationError({"code": "INTEREST_LIMIT", "message": "You can select a maximum of 10 interests."})
            
        return value

class LocationUpdateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(source='location_latitude', required=False, allow_null=True)
    longitude = serializers.FloatField(source='location_longitude', required=False, allow_null=True)
    
    class Meta:
        model = Profile
        fields = ['latitude', 'longitude', 'city', 'country', 'location_enabled']

    def validate(self, data):
        lat = data.get('location_latitude')
        lon = data.get('location_longitude')
        
        if lat is not None and (lat < -90 or lat > 90):
            raise ValidationError({"code": "INVALID_LOCATION", "message": "Latitude must be between -90 and 90."})
        if lon is not None and (lon < -180 or lon > 180):
            raise ValidationError({"code": "INVALID_LOCATION", "message": "Longitude must be between -180 and 180."})
            
        return data

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['notifications_enabled', 'notifications_permission_status']

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ['minimum_age', 'maximum_age', 'maximum_distance_km', 'preferred_genders']

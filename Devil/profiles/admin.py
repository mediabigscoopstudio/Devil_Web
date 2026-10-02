from django.contrib import admin
from .models import Profile, ProfilePhoto, Interest, DatingIntent, Preference

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'gender', 'profile_completed', 'is_discoverable', 'created_at', 'updated_at')
    list_filter = ('profile_completed', 'gender', 'is_discoverable')
    search_fields = ('display_name', 'user__phone_number', 'user__email')

@admin.register(ProfilePhoto)
class ProfilePhotoAdmin(admin.ModelAdmin):
    list_display = ('profile', 'is_primary', 'sort_order', 'created_at')

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'sort_order')
    list_filter = ('is_active',)

@admin.register(DatingIntent)
class DatingIntentAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'is_active', 'sort_order')
    list_filter = ('is_active',)

@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'minimum_age', 'maximum_age', 'maximum_distance_km')

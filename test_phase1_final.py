import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Devil.settings')
import sys
sys.path.append('/Volumes/Juggernut_Assist/Projects/Devil/Devil_web/Devil')
django.setup()

from rest_framework.test import APIClient
from django.test import Client
from accounts.models import User
from moderation.models import Report

def run_phase1_final_test():
    print("--- STARTING PHASE 1 FINAL ACCEPTANCE VERIFICATION ---")

    # 1. Create Superuser for Dashboard Test
    admin_user, _ = User.objects.get_or_create(
        phone_number='+910000000000',
        defaults={'is_staff': True, 'is_superuser': True, 'is_active': True}
    )
    admin_user.set_password('AdminPassword123')
    admin_user.save()

    # 2. Super Admin Dashboard Security Checks
    web_client = Client()
    # Anonymous request to dashboard -> redirect to login
    dash_resp = web_client.get('/')
    assert dash_resp.status_code == 302 and '/login/' in dash_resp.url, "Anonymous user should be redirected to login"

    # Login with Superuser
    login_resp = web_client.post('/login/', {'phone_number': '+910000000000', 'password': 'AdminPassword123'})
    assert login_resp.status_code == 302, "Superuser login should succeed"

    # View Dashboard Home & Users
    home_resp = web_client.get('/')
    assert home_resp.status_code == 200, "Superuser should access Dashboard Home"

    # 3. User A & User B Mobile API Operations
    client_a = APIClient()
    client_b = APIClient()

    res_a_v = client_a.post('/api/v1/auth/verify-otp/', {'phone_number': '+918888888881', 'otp': '00000'})
    token_a = res_a_v.data['access']
    client_a.credentials(HTTP_AUTHORIZATION='Bearer ' + token_a)

    res_b_v = client_b.post('/api/v1/auth/verify-otp/', {'phone_number': '+918888888882', 'otp': '00000'})
    token_b = res_b_v.data['access']
    client_b.credentials(HTTP_AUTHORIZATION='Bearer ' + token_b)

    user_a_id = res_a_v.data['user_id']
    user_b_id = res_b_v.data['user_id']

    # Onboarding
    client_a.post('/api/v1/profile/', {'display_name': 'Anna', 'gender': 'Female', 'bio': 'Artist'})
    client_b.post('/api/v1/profile/', {'display_name': 'Ben', 'gender': 'Male', 'bio': 'Developer'})

    # Swipe & Match
    client_a.post('/api/v1/discovery/swipe/', {'target_user_id': str(user_b_id), 'action': 'LIKE'})
    swipe_b = client_b.post('/api/v1/discovery/swipe/', {'target_user_id': str(user_a_id), 'action': 'LIKE'})
    assert swipe_b.data['matched'] == True, "Reciprocal swipe must trigger match"

    # Conversation & Message
    convs = client_a.get('/api/v1/conversations/').data
    conv_id = convs[0]['id']
    client_a.post(f'/api/v1/conversations/{conv_id}/messages/', {'text': 'Hey Ben!'})

    # Report & Block
    report_res = client_a.post('/api/v1/moderation/reports/', {'reported_user_id': str(user_b_id), 'reason': 'Spam'})
    assert report_res.status_code == 201, "User report should succeed"

    block_res = client_a.post('/api/v1/moderation/blocks/', {'blocked_user_id': str(user_b_id)})
    assert block_res.status_code == 201, "User block should succeed"

    # Super Admin manages Report & Suspends User
    reports_dash = web_client.get('/reports/')
    assert reports_dash.status_code == 200, "Superuser should see reports"

    suspend_resp = web_client.get(f'/users/{user_b_id}/suspend/')
    assert suspend_resp.status_code == 302, "Superuser can suspend user"

    user_b_obj = User.objects.get(id=user_b_id)
    assert user_b_obj.status == 'SUSPENDED', "User B status should be SUSPENDED"

    print("--- ALL PHASE 1 FINAL ACCEPTANCE TESTS PASSED SUCCESSFULLY! ---")

if __name__ == '__main__':
    run_phase1_final_test()

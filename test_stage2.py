import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Devil.settings')
import sys
sys.path.append('/Volumes/Juggernut_Assist/Projects/Devil/Devil_web/Devil')
django.setup()

from rest_framework.test import APIClient
from accounts.models import User
from profiles.models import Profile

def run_test():
    client_a = APIClient()
    client_b = APIClient()

    # 1. Auth A
    res_a = client_a.post('/api/v1/auth/request-otp/', {'phone_number': '+919999999991'})
    res_a_v = client_a.post('/api/v1/auth/verify-otp/', {'phone_number': '+919999999991', 'otp': '00000'})
    token_a = res_a_v.data['access']
    client_a.credentials(HTTP_AUTHORIZATION='Bearer ' + token_a)

    # 2. Auth B
    res_b = client_b.post('/api/v1/auth/request-otp/', {'phone_number': '+919999999992'})
    res_b_v = client_b.post('/api/v1/auth/verify-otp/', {'phone_number': '+919999999992', 'otp': '00000'})
    token_b = res_b_v.data['access']
    client_b.credentials(HTTP_AUTHORIZATION='Bearer ' + token_b)

    user_a_id = res_a_v.data['user_id']
    user_b_id = res_b_v.data['user_id']

    # 3. Setup Profiles
    client_a.post('/api/v1/profile/', {'display_name': 'Alice', 'gender': 'Female', 'bio': 'Hey there'})
    client_b.post('/api/v1/profile/', {'display_name': 'Bob', 'gender': 'Male', 'bio': 'Hello world'})

    # 4. A swipes LIKE on B
    swipe_a = client_a.post('/api/v1/discovery/swipe/', {'target_user_id': str(user_b_id), 'action': 'LIKE'})
    assert swipe_a.data['matched'] == False, "A should not be matched yet"

    # 5. B swipes LIKE on A
    swipe_b = client_b.post('/api/v1/discovery/swipe/', {'target_user_id': str(user_a_id), 'action': 'LIKE'})
    assert swipe_b.data['matched'] == True, "B reciprocal swipe should trigger match"
    match_id = swipe_b.data['match_id']

    # 6. Check Matches & Conversations
    matches_a = client_a.get('/api/v1/matches/')
    assert len(matches_a.data) == 1, "Alice should have 1 match"

    convs_a = client_a.get('/api/v1/conversations/')
    assert len(convs_a.data) == 1, "Alice should have 1 conversation"
    conv_id = convs_a.data[0]['id']

    # 7. Alice sends message to Bob
    msg_res = client_a.post(f'/api/v1/conversations/{conv_id}/messages/', {'text': 'Hi Bob!'})
    assert msg_res.status_code == 201

    # 8. Bob reads message
    bob_msgs = client_b.get(f'/api/v1/conversations/{conv_id}/messages/')
    assert len(bob_msgs.data) == 1
    assert bob_msgs.data[0]['text'] == 'Hi Bob!'

    print("STAGE 2 E2E TEST PASSED FULLY! All APIs verified.")

if __name__ == '__main__':
    run_test()

from django.db import migrations

def seed_data(apps, schema_editor):
    DatingIntent = apps.get_model('profiles', 'DatingIntent')
    Interest = apps.get_model('profiles', 'Interest')
    
    intents = [
        ('casual_date', 'Casual dating'),
        ('open_relationship', 'Open relationship'),
        ('friends_with_benefits', 'Friends with benefits'),
        ('exploring', 'Exploring'),
        ('long_term_open', 'Long term open'),
        ('not_sure_yet', 'Not sure yet'),
    ]
    
    for i, (code, label) in enumerate(intents):
        DatingIntent.objects.get_or_create(
            code=code,
            defaults={'label': label, 'sort_order': i}
        )
        
    interests = [
        'Travel', 'Music', 'Food', 'Fitness', 'Art', 'Parties',
        'Photography', 'Anime', 'Books', 'Movies', 'Dancing', 'Gaming'
    ]
    
    for i, name in enumerate(interests):
        slug = name.lower()
        Interest.objects.get_or_create(
            name=name,
            defaults={'slug': slug, 'sort_order': i}
        )

class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_datingintent_remove_profile_location_name_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_data),
    ]

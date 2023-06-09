# Generated by Django 4.2 on 2023-05-24 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TranscribeVideoDB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_id', models.TextField()),
                ('transcribe_data', models.JSONField()),
                ('playlist_id', models.TextField(null=True)),
                ('video_title', models.TextField(null=True)),
                ('channel_title', models.TextField(null=True)),
                ('channel_url', models.TextField(null=True)),
            ],
        ),
    ]

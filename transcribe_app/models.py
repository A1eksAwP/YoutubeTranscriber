from django.db import models


class TranscribeVideoDB(models.Model):
    video_id = models.TextField(null=False)
    transcribe_data = models.JSONField()
    playlist_id = models.TextField(null=True)
    video_title = models.TextField(null=True)
    channel_title = models.TextField(null=True)
    channel_url = models.TextField(null=True)

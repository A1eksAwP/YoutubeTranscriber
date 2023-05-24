import json
import re

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseNotModified
from django.shortcuts import render, redirect

from transcribe_app.models import TranscribeVideoDB
from transcribe_app.service.parsers.youtube_transcriber import YouTubeTranscriber
from pytube import Playlist as YouTubePlaylist
from transcribe_app.service.exceptions import ERROR_MESSAGE


def main(request: WSGIRequest):
    return render(request, 'transcribe.html')


def single_video(request: WSGIRequest):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        transcript_obj = YouTubeTranscriber(video_url)
        if transcript_obj.errors_list:
            return render(request, 'transcribe.html', {
                'errors': transcript_obj.errors_list,
            })
        return render(request, 'video.html', {
            'video_id': transcript_obj.video_id,
            'transcriptions': transcript_obj.transcript_dict,
            'video_title': transcript_obj.video_title,
            'channel_title': transcript_obj.channel_title,
            'channel_url': transcript_obj.channel_url,
        })


def playlist(request: WSGIRequest):
    if request.method == 'POST':
        playlist_url = request.POST.get('playlist_url')
        if not re.fullmatch(r'(https://)?(www\.)?youtube\.com/playlist\?list=\S*', playlist_url):
            return render(request, 'transcribe.html', {
                'errors': [ERROR_MESSAGE.BAD_PLAYLIST_URL],
            })
        video_urls = YouTubePlaylist(playlist_url)
        video_transcriptions, videos_id = [], []
        errors_dict = dict()
        playlist_id = 1
        for video_url in video_urls:
            transcript_obj = YouTubeTranscriber(video_url, playlist_id)
            if transcript_obj.errors_list:
                errors_dict[playlist_id] = {
                    'video_id': transcript_obj.get_video_id(),
                    'video_url': transcript_obj.video_url,
                    'description': "; ".join(transcript_obj.errors_list)
                }
            video_transcriptions.append(transcript_obj.get_transcriptions())
            videos_id.append(transcript_obj.get_video_id())
            playlist_id += 1
        return render(request, 'playlist.html', {
            'videos': {
                'transcriptions': video_transcriptions,
                'videos_id': videos_id,
            },
            'id_ok_count': f'{len(videos_id) - len(errors_dict)}/{len(videos_id)}',
            'errors': errors_dict,
        })


def save_data_base(request: WSGIRequest):
    if request.method == 'POST':
        apply_objects = [key for key in request.POST.keys() if key != 'csrfmiddlewaretoken']
        apply_dict = dict()
        for obj in apply_objects:
            video_id, timecode = obj.split('?')
            if apply_dict.get(video_id):
                apply_dict[video_id] += [timecode]
            else:
                apply_dict[video_id] = [timecode]
        for video_id in apply_dict:
            db_transcribe: TranscribeVideoDB = TranscribeVideoDB.objects.filter(video_id=video_id).first()
            transcript_dict = json.loads(db_transcribe.transcribe_data)
            for timecode in apply_dict[video_id]:
                transcript_dict[timecode]['is_used'] = True
            db_transcribe.transcribe_data = json.dumps(transcript_dict)
            db_transcribe.save()
    return HttpResponseNotModified()

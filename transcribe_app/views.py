import json
import re
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseNotModified
from django.shortcuts import render
from transcribe_app.models import TranscribeVideoDB
from transcribe_app.service.parsers.youtube_transcriber import YouTubeTranscriber
from pytube import Playlist as YouTubePlaylist
from transcribe_app.service.exceptions import ERROR_MESSAGE


def main(request: WSGIRequest):
    all_transcribes: TranscribeVideoDB = TranscribeVideoDB.objects.all()
    return render(request, 'transcribe.html', {'db_transcribes': all_transcribes})


def load_from_db(request: WSGIRequest):
    if request.method == 'POST':
        video_id = request.POST.get('video_id')
        return single_video(request, f'https://www.youtube.com/watch?v={video_id}')


def try_request(request: WSGIRequest):
    if request.method == 'POST':
        user_url = request.POST.get('user_url')
        if re.fullmatch(r'(https://)?(www\.)?youtube\.com/playlist\?list=\S*', user_url):
            return playlist(request, user_url)
        elif re.fullmatch(r'(https://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)\S*', user_url):
            return single_video(request, user_url)
        else:
            return render(request, 'transcribe.html', {
                'errors': [ERROR_MESSAGE.BAD_URL],
            })


def single_video(request: WSGIRequest, video_url):
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


def playlist(request: WSGIRequest, playlist_url):
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


def save_db(request: WSGIRequest):
    if request.method == 'POST':
        cash_set = {key[5:] for key in request.POST.keys() if key.startswith('cash?')}
        apply_set = {
            key for key in request.POST.keys() if not (key.startswith('csrfmiddlewaretoken') or key.startswith('cash?'))
        }
        canceled_set = cash_set.difference(apply_set)
        used_phrase = dict()
        for new_obj in apply_set:
            video_id, time = new_obj.split('?')
            used_phrase[video_id] = used_phrase[video_id] + [time] if used_phrase.get(video_id) else [time]
        cancel_phrase = dict()
        for obj in canceled_set:
            video_id, time = obj.split('?')
            cancel_phrase[video_id] = cancel_phrase[video_id] + [time] if cancel_phrase.get(video_id) else [time]
        for video_id in used_phrase:
            db_transcribe: TranscribeVideoDB = TranscribeVideoDB.objects.filter(video_id=video_id).first()
            transcript_dict = json.loads(db_transcribe.transcribe_data)
            for time in used_phrase[video_id]:
                transcript_dict[time]['is_used'] = True
            db_transcribe.transcribe_data = json.dumps(transcript_dict)
            db_transcribe.save()
        for video_id in cancel_phrase:
            db_transcribe: TranscribeVideoDB = TranscribeVideoDB.objects.filter(video_id=video_id).first()
            transcript_dict = json.loads(db_transcribe.transcribe_data)
            for time in cancel_phrase[video_id]:
                transcript_dict[time]['is_used'] = False
            db_transcribe.transcribe_data = json.dumps(transcript_dict)
            db_transcribe.save()
    return HttpResponseNotModified()

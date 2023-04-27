from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from transcribe_app.service.parsers.youtube_transcriber import YouTubeTranscriber
from pytube import Playlist as YouTubePlaylist


def main(request: WSGIRequest):
    return render(request, 'main.html')


def single_video(request: WSGIRequest):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        transcript_obj = YouTubeTranscriber(video_url)
        if transcript_obj.errors_list:
            return render(request, 'main.html', {
                'errors': transcript_obj.errors_list,
            })
        transcriptions = transcript_obj.transcript_dict
        video_id = transcript_obj.video_id
        video_title = transcript_obj.video_title
        channel_title = transcript_obj.channel_title
        channel_url = transcript_obj.channel_url
        return render(request, 'video.html', {
            'video_id': video_id,
            'transcriptions': transcriptions,
            'video_title': video_title,
            'channel_title': channel_title,
            'channel_url': channel_url,
        })


def channel(request: WSGIRequest):
    if request.method == 'POST':
        playlist_url = request.POST.get('playlist_url')
        video_urls = YouTubePlaylist(playlist_url)
        errors_list = []
        video_transcriptions = []
        videos_id = []
        playlist_id = 0
        for video_url in video_urls:
            transcript_obj = YouTubeTranscriber(video_url, playlist_id)
            if transcript_obj.errors_list:
                errors_list.append(
                    f'Для №{playlist_id} из плейлиста возникли ошибки: {"; ".join(transcript_obj.errors_list)}'
                )
            transcriptions = transcript_obj.get_transcriptions()
            video_id = (transcript_obj.get_video_id(), playlist_id)
            video_transcriptions.append(transcriptions)
            videos_id.append(video_id)
            playlist_id += 1
        return render(request, 'playlist.html', {
            'videos': {
                'transcriptions': video_transcriptions,
                'videos_id': videos_id,
            },
            'video_count': f'{len(videos_id) - len(errors_list)}/{len(videos_id)}',
            'errors': errors_list,
        })

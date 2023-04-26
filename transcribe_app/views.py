from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from transcribe_app.service.parsers.youtube_transcriber import YouTubeTranscriber, BadUrlError


def main(request: WSGIRequest):
    return render(request, 'main.html')


def video(request: WSGIRequest):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        try:
            transcript_obj = YouTubeTranscriber(video_url)
        except BadUrlError as ex:
            return render(request, 'main.html', {
                'errors': ex.message,
            })
        transcriptions = transcript_obj.transcript_dict
        video_id = transcript_obj.video_id
        video_title = transcript_obj.video_title.decode('utf-8')
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
        channel_url = request.POST.get('channel_url')
        ...
        video_url_1 = 'https://www.youtube.com/watch?v=AtZROpdj7DE'
        video_url_2 = 'https://www.youtube.com/watch?v=43yoYayn1CE'
        video_url_3 = 'https://www.youtube.com/watch?v=Lv3gv-IXBq0'
        video_urls = (video_url_1, video_url_2, video_url_3)
        video_transcriptions = []
        videos_id = []
        for video_url in video_urls:
            transcript_obj = YouTubeTranscriber(video_url)
            transcriptions = transcript_obj.get_transcriptions()
            video_id = transcript_obj.get_video_id()
            video_transcriptions.append(transcriptions)
            videos_id.append(video_id)
        return render(request, 'channel.html', {
            'videos': video_transcriptions,
            'videos_id': videos_id,
        })

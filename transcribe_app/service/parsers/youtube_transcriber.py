"""
This is my simple parser for automatic made KATA.py files to solution a new kata from codewars URL.
"""
import requests
import json
import re


class YouTubeTranscriber:
    def __init__(self, video_url: str):
        self.video_url = self.validate_url(video_url)
        self.video_id = self.set_video_id()
        self.params = ''
        self.api_key = ''
        self.video_title = ''
        self.channel_title = ''
        self.channel_url = ''
        self.transcript_url = f'https://www.youtube.com/youtubei/v1/get_transcript?key={self.api_key}'
        self.html = None
        self.transcript_json = None
        self.transcript_dict = dict()
        self.transcribe()

    @staticmethod
    def validate_url(video_url: str) -> str:
        if not re.fullmatch(r'(https://)?www\.youtube\.com/watch\?v=[^&]+.*', video_url):
            raise BadUrlError(video_url)
        return video_url

    def set_video_id(self):
        return re.search(r'/watch\?v=(?P<id>[^&]+)', self.video_url).group('id')

    def start_parser(self):
        self.html = str(requests.get(self.video_url).content)
        self._set_params()
        self._set_api_key()
        self._get_transcript_json()
        self._get_transcript_dict()

    def transcribe(self):
        self.start_parser()
        self._set_video_title()
        self._set_channel_title()
        self._set_channel_url()

    def _set_params(self):
        try:
            self.params = re.search('"serializedShareEntity":"(?P<p>[A-Za-z0-9%]*)"', self.html).group('p')
        except AttributeError:
            raise MissingParamsError

    def _set_api_key(self):
        try:
            self.api_key = re.search('"innertubeApiKey":"(?P<k>[A-Za-z0-9_]*)"', self.html).group('k')
        except AttributeError:
            raise MissingApiKeyError

    def _set_video_title(self):
        try:
            self.video_title = re.search('<meta name="title" content="(?P<t>[^"]+)"', self.html).group('t').encode('utf-8')
        except AttributeError:
            raise MissingApiKeyError

    def _set_channel_title(self):
        try:
            self.channel_title = re.search('<span itemprop="author".+content="(?P<ct>[^"]+)"', self.html).group('ct')
        except AttributeError:
            raise MissingApiKeyError

    def _set_channel_url(self):
        try:
            self.channel_url = re.search('<span itemprop="author".+href="(?P<cu>[^"]+)"', self.html).group('cu')
        except AttributeError:
            raise MissingApiKeyError

    def _get_transcript_json(self):
        agent_params = {
            "context": {
                "client": {
                    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
                    "clientName": "WEB",
                    "clientVersion": "2.20220309.01.00",
                }
            },
            "params": f"{self.params}",
        }
        response = requests.post(self.transcript_url, json=agent_params)
        if response.status_code != 200:
            response.raise_for_status()
        self.transcript_json = json.loads(response.content)
        if "actions" not in self.transcript_json.keys():
            raise MissingTranscriptError(self.api_key, self.params)

    def _navigate_to_cue_groups(self) -> dict[any, any]:
        return self.transcript_json["actions"][0]["updateEngagementPanelAction"]["content"][
            "transcriptRenderer"
            ]["body"]["transcriptBodyRenderer"]["cueGroups"]

    @staticmethod
    def _parse_cue_group(cue_group: dict) -> tuple[str, str]:
        time = cue_group["transcriptCueGroupRenderer"]["formattedStartOffset"]["simpleText"]
        phrase = cue_group["transcriptCueGroupRenderer"]["cues"][0]["transcriptCueRenderer"]["cue"]["simpleText"]
        return time, phrase

    def _get_transcript_dict(self):
        self.transcript_json = self._navigate_to_cue_groups()
        for cue_group in self.transcript_json:
            time_code, phrase = self._parse_cue_group(cue_group)
            time_seconds = self.get_sec(time_code)
            self.transcript_dict[time_code] = (phrase, time_seconds)

    def get_transcriptions(self) -> dict[str]:
        return self.transcript_dict

    def get_video_id(self) -> str:
        return self.video_id

    @staticmethod
    def get_sec(time: str) -> int:
        sec = 0
        for duration in time.split(":"):
            sec = sec * 60 + int(duration)
        return sec


class MissingTranscriptError(BaseException):
    def __init__(self, api_key, params):
        self.api_key = api_key
        self.params = params
        self.message = f'key: "{self.api_key}", param: "{self.params}"'
        super().__init__(self.message)


class MissingApiKeyError(BaseException):
    def __init__(self):
        super().__init__()


class MissingParamsError(BaseException):
    def __init__(self):
        super().__init__()


class BadUrlError(BaseException):
    def __init__(self, video_url):
        self.video_url = video_url
        self.message = f'Ваша ссылка "{self.video_url}" не является url видео из YouTube'
        super().__init__()

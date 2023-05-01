import requests
import json
import re
import ast
from transcribe_app.service.exceptions import errors as exception
from transcribe_app.service.exceptions import ERROR_MESSAGE


class YouTubeTranscriber:
    """
    This my simple parser for automatic made transcribes with timecodes from GET and POST in YouTube.com URL.

    How it works a step by step:

    1. Validate your URL like real YouTube video
    2. Parse video_id from URL
    3. GET to video url
    4. Find api key and params in response HTML
    5. Set new JSON object with params and user-agent
    6. POST to transcript_url with your api_key
    7. Parse "transcriptCueGroupRenderer"..."simpleText" in JSON response
    8. Modify every timecodes "HH:MM:SS" to "...s" formats
    9. Write your complete transcript_dict
    """

    def __init__(self, url: str, playlist_id: int = 1):
        self.url = url
        self.video_id = ''
        self.params = ''
        self.api_key = ''
        self.video_title = ''
        self.channel_title = ''
        self.channel_url = ''
        self.video_url = ''
        self.transcript_url = ''
        self.playlist_id = playlist_id
        self.html = None
        self.transcript_json = None
        self.transcript_dict = dict()
        self.errors_list = []
        self.transcribe()

    @staticmethod
    def validate_url(url: str) -> str:
        if not re.fullmatch(r'(https://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)\S*', url):
            raise exception.BadUrlError(url)
        return url

    def set_video_id(self):
        return re.search(r'/watch\?v=(?P<id>[^&]+)', self.url).group('id')

    def transcribe(self):
        try:
            self.start_parser()
        except exception.BadUrlError:
            self.errors_list.append(ERROR_MESSAGE.BAD_URL)
        except exception.BadRequest:
            self.errors_list.append(ERROR_MESSAGE.BAD_REQUEST)
        except exception.MissingApiKeyError:
            self.errors_list.append(ERROR_MESSAGE.MISSING_API_KEY)
        except exception.MissingParamsError:
            self.errors_list.append(ERROR_MESSAGE.MISSING_PARAMS)
        except exception.MissingTranscriptError:
            self.errors_list.append(ERROR_MESSAGE.MISSING_TRANSCRIPT)
        except exception.MissingViTitleError:
            self.errors_list.append(ERROR_MESSAGE.MISSING_VD_TITTLE)
        except exception.MissingChTitleError:
            self.errors_list.append(ERROR_MESSAGE.MISSING_CH_TITTLE)
        except exception.MissingChUrlError:
            self.errors_list.append(ERROR_MESSAGE.MISSING_CH_URL)

    def start_parser(self):
        self.url = self.validate_url(self.url)
        self.video_id = self.set_video_id()
        self.video_url = f'https://www.youtube.com/watch?v={self.video_id}'
        self._set_html()
        self._set_params()
        self._set_api_key()
        self.transcript_url = f'https://www.youtube.com/youtubei/v1/get_transcript?key={self.api_key}'
        self._get_transcript_json()
        self._set_transcript_dict()
        self._set_video_title()
        self._set_channel_title()
        self._set_channel_url()

    def _set_html(self):
        response = requests.get(self.video_url)
        if response.status_code != 200:
            raise exception.BadRequest
        self.html = str(response.content)

    def _set_params(self):
        try:
            self.params = re.search('"serializedShareEntity":"(?P<p>[A-Za-z0-9%]*)"', self.html).group('p')
        except AttributeError:
            raise exception.MissingParamsError

    def _set_api_key(self):
        try:
            self.api_key = re.search('"innertubeApiKey":"(?P<k>[A-Za-z0-9_]*)"', self.html).group('k')
        except AttributeError:
            raise exception.MissingApiKeyError

    def _set_video_title(self):
        try:
            self.video_title = re.search('<meta name="title" content="(?P<t>[^"]+)"', self.html).group('t')
        except AttributeError:
            raise exception.MissingViTitleError
        # Далее придется применять перекодирование через ast, поскольку иначе мы получим двойное экранирование в b'\\'
        self.video_title = ast.literal_eval(f"b'{self.video_title}'").decode('utf-8')

    def _set_channel_title(self):
        try:
            self.channel_title = re.search('"author":"(?P<ct>[^"]+)"', self.html).group('ct')
        except AttributeError:
            raise exception.MissingChTitleError
        # Далее придется применять перекодирование через ast, поскольку иначе мы получим двойное экранирование в b'\\'
        self.channel_title = ast.literal_eval(f"b'{self.channel_title}'").decode('utf-8')

    def _set_channel_url(self):
        try:
            self.channel_url = re.search('"ownerProfileUrl":"(?P<cu>[^"]+)"', self.html).group('cu')
        except AttributeError:
            raise exception.MissingChUrlError

    def _get_transcript_json(self):
        agent_params = {
            "context": {
                "client": {
                    "h1": "ru",
                    "gl": "RU",
                    "timeZone": "Europe/Moscow",
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
            raise exception.MissingTranscriptError(self.api_key, self.params)

    def _navigate_to_cue_groups(self) -> dict[any, any]:
        return self.transcript_json["actions"][0]["updateEngagementPanelAction"]["content"][
            "transcriptRenderer"
            ]["body"]["transcriptBodyRenderer"]["cueGroups"]

    @staticmethod
    def _parse_cue_group(cue_group: dict) -> tuple[str, str]:
        time = cue_group["transcriptCueGroupRenderer"]["formattedStartOffset"]["simpleText"]
        phrase = cue_group["transcriptCueGroupRenderer"]["cues"][0]["transcriptCueRenderer"]["cue"]["simpleText"]
        return time, phrase

    def _set_transcript_dict(self):
        self.transcript_json = self._navigate_to_cue_groups()
        for cue_group in self.transcript_json:
            time_code, phrase = self._parse_cue_group(cue_group)
            time_seconds = self.time_to_sec(time_code)
            self.transcript_dict[time_code] = (phrase, time_seconds, self.video_id, self.playlist_id)

    def get_transcriptions(self) -> dict[str]:
        return self.transcript_dict

    def get_video_id(self) -> str:
        return self.video_id

    @staticmethod
    def time_to_sec(time: str) -> int:
        sec = 0
        for duration in time.split(":"):
            sec = sec * 60 + int(duration)
        return sec

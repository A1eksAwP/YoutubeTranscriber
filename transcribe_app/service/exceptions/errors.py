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


class MissingViTitleError(BaseException):
    def __init__(self):
        super().__init__()


class MissingChTitleError(BaseException):
    def __init__(self):
        super().__init__()


class MissingChUrlError(BaseException):
    def __init__(self):
        super().__init__()


class BadUrlError(BaseException):
    def __init__(self, video_url):
        self.video_url = video_url
        self.message = f'Ваша ссылка "{self.video_url}" не является url видео из YouTube'
        super().__init__()


class BadRequest(BaseException):
    def __init__(self):
        super().__init__()
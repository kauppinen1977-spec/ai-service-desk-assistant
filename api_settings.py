"""Process-local API settings. Secrets are never persisted or returned by status()."""
import os
import re
import threading


def validate_key(key):
    from desk import DeskError
    if not isinstance(key, str) or not 1 <= len(key.strip()) <= 512 or any(ord(c) < 33 or ord(c) > 126 for c in key.strip()):
        raise DeskError('API-avaimen muoto ei kelpaa.', 'invalid_key_format', 400,
                        'Liitä API-asetuksiin pelkkä avain ilman lainausmerkkejä tai sisäisiä välilyöntejä. Avainta ei testattu palvelussa.')
    if key.strip().startswith(('"', "'")) or key.strip().endswith(('"', "'")):
        raise DeskError('API-avaimen ympärillä on lainausmerkit.', 'invalid_key_format', 400,
                        'Poista lainausmerkit ja ota asetus uudelleen käyttöön.')
    return key.strip()


class APISettings:
    def __init__(self):
        self._lock = threading.RLock()
        self._key = None  # None uses the server's inherited environment.
        self._model = None
        self._revision = 0
        self._result = 'not_tested'

    def snapshot(self):
        with self._lock:
            key = (os.environ.get('OPENAI_API_KEY', '') if self._key is None else self._key).strip()
            model = self._model or os.environ.get('OPENAI_MODEL', '').strip() or 'gpt-4.1-mini'
            return key, model, self._revision

    def status(self):
        with self._lock:
            key, model, _ = self.snapshot()
            return {'configured': bool(key), 'source': ('environment' if self._key is None else 'local') if key else 'none',
                    'model': model, 'persistence': 'process_memory', 'last_result': self._result}

    def update(self, obj):
        from desk import DeskError
        with self._lock:
            if obj.get('clear') is True:
                self._key = ''  # Do not silently fall back to an inherited, possibly stale key.
            else:
                key = validate_key(obj.get('api_key'))
                model = obj.get('model', self.snapshot()[1])
                if not isinstance(model, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._:-]{0,119}', model.strip()) or model.strip().startswith('sk-'):
                    raise DeskError('Mallin tunniste ei kelpaa.', 'invalid_model_setting', 400,
                                    'Kirjoita API-projektissasi käytettävissä olevan mallin tunniste.')
                self._key, self._model = key.strip(), model.strip()
            self._revision += 1
            self._result = 'not_tested'
            return self.status()

    def record(self, revision, result):
        with self._lock:
            if revision == self._revision:
                self._result = result


settings = APISettings()

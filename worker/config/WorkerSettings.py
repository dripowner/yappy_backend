from api.config.ArqSettings import arqsettings
from worker.models_worker import analyze_requests


class WorkerSettings:
    functions = [analyze_requests]
    redis_settings = arqsettings

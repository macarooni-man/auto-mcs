def _unsupported(*args, **kwargs):
    raise RuntimeError("bcrypt server operations are unavailable on the Android Telepath client")


gensalt = _unsupported
hashpw = _unsupported
checkpw = _unsupported

class MegafonError(RuntimeError):
    pass


class AuthenticationError(MegafonError):
    pass


class CaptchaRequired(AuthenticationError):
    pass


class AccountBlocked(AuthenticationError):
    pass


class SessionExpired(AuthenticationError):
    pass


class ProtocolChanged(MegafonError):
    pass

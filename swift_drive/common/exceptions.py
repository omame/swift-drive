class Error(StandardError):
    """
    Base class for all errors and exceptions
    """
    pass


class ResponseError(Error):
    """
    A General response error
    """
    def __init__(self, status, reason):
        self.status = status
        self.reason = reason
        Error.__init__(self)

    def __str__(self):
        return '%d - %s' % (self.status, self.reason)

    def __repr__(self):
        return '%d - %s' % (self.status, self.reason)

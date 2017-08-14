# -*- coding: utf-8 -*-
"""
Copyright 2017 Martin Picard
MIT License
"""


class EurekaClientException(Exception):
    pass


class RegistrationFailed(EurekaClientException):
    pass


class UpdateFailed(EurekaClientException):
    pass


class HeartbeatFailed(EurekaClientException):
    pass


class FetchFailed(EurekaClientException):
    pass


class ConfigurationException(EurekaClientException):
    pass

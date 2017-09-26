# -*- coding: utf-8 -*-
# Copyright 2017 Martin Picard
# MIT License
import pytest
from eureka_client import Client


@pytest.fixture(scope="function")
def client(request):
    return Client('test', eureka_url='http://eureka:8080/eureka/v2')

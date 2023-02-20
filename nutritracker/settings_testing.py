#!/usr/bin/python

from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'nutritracker_test',
        'USER': config("DB_USERNAME"),
        'PASSWORD': config("DB_PASSWORD"),
        'HOST': 'localhost',
        'PORT': 27017
    }
}

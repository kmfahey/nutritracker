#!/usr/bin/python

from djongo import models

# Create your models here.


class Account(models.Model):
    __columns__ = ('_id', 'username', 'password_encrypted', 'display_name', 'gender_at_birth', 'gender_identity',
                   'pronouns', 'age', 'height', 'weight', 'activity_level', 'weight_goal')

    _id                 = models.ObjectIdField(primary_key=True)
    username            = models.CharField(max_length=32,       default="",  verbose_name="Username")
                        # This is a Binary object because bcrypt.hashpw and bcrypt.checkpw take
                        # their arguments as bytes objects, not str
    password_encrypted  = models.BinaryField(max_length=80,     default=b'', verbose_name="Password")
    display_name        = models.CharField(max_length=200,      default="",  verbose_name="Display name")
    gender_at_birth     = models.CharField(max_length=1,        default="",  verbose_name="Gender at birth")
    gender_identity     = models.CharField(max_length=200,      default="",  verbose_name="Gender identity")
    pronouns            = models.CharField(max_length=200,      default="",  verbose_name="Pronouns")
    age                 = models.PositiveSmallIntegerField(     default=0,   verbose_name="Age")
    height              = models.FloatField(                    default=0.0, verbose_name="Height")
    weight              = models.FloatField(                    default=0.0, verbose_name="Weight")
    activity_level      = models.PositiveSmallIntegerField(     default=0,   verbose_name="Activity level (1-5)")
    weight_goal         = models.SmallIntegerField(             default=0,   verbose_name="Weight goal")

    class Meta:
        managed = False
        db_table = 'accounts'
        app_label = 'users'


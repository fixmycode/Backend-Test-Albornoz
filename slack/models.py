from hashlib import sha1
from django.db import models


class SlackManager(models.Manager):
    def create(*args, **kwargs):
        singleton = SlackIdentity.load()
        for field, value in kwargs.items():
            setattr(singleton, field, value)
        singleton.save()
        return singleton


class SlackIdentity(models.Model):
    """A singleton model that stores the information about the
    user that installed the application"""
    user_id = models.CharField(max_length=256)
    team_id = models.CharField(max_length=256)
    access_token = models.CharField(max_length=256)

    objects = SlackManager()

    class Meta:
        unique_together = [('user_id', 'team_id', 'access_token'), ]

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SlackIdentity, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def get_identity_hash(cls):
        identity = cls.load()
        hasher = sha1()
        line = identity.user_id+identity.team_id+identity.access_token
        hasher.update(line.encode('utf-8'))
        return hasher.hexdigest()

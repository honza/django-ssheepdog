from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.utils import DatabaseError
from fabric.api import env, run
import os
from django.conf import settings
from ssheepdog.utils import read_file

root = getattr(settings, 'PROJECT_ROOT', None)
KEYS_DIR = os.path.join(root, '../deploy/keys')

class UserProfile(models.Model):
    nickname = models.CharField(max_length=256)
    user = models.OneToOneField(User, primary_key=True, related_name='_profile_cache')
    ssh_key = models.TextField()
    is_active = models.BooleanField()

    def __str__(self):
        return self.nickname

    def __unicode__(self):
        return self.nickname or self.user.username

class Machine(models.Model):
    # XXX: A machine should have either an IP or hostname or both
    # Need a validator in the form supplied to the django admin
    # Consider validating on save as well... not as important
    nickname = models.CharField(max_length=256)
    hostname = models.CharField(max_length=256, blank=True, null=True)
    ip = models.CharField(max_length=256, null=True, blank=True)
    description = models.TextField()
    port = models.IntegerField(default=22)
    client = models.ForeignKey('Client', null=True, blank=True)
    is_down = models.BooleanField(default=False)
    is_active = models.BooleanField()

    def __unicode__(self):
        return self.nickname

class Login(models.Model):
    machine = models.ForeignKey('Machine')
    username = models.CharField(max_length=256)
    users = models.ManyToManyField(User, blank=True)
    client = models.ForeignKey('Client', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_dirty = models.BooleanField(default=True)

    def __unicode__(self):
        return self.username

    def get_authorized_keys(self):
        """
        Return a list of authorized keys strings which should be deployed
        to the machine.
        """
        keys = [read_file(os.path.join(KEYS_DIR, 'application.pub'))]
        if self.is_active and self.machine.is_active:
            for user in (self.users
                         .filter(is_active = True)
                         .select_related('_profile_cache')):
                keys.append(user.get_profile().ssh_key)
        return keys

    def update_keys(self): 
        """
        Updates the authorized_keys file on the machine attached to this login 
        adding or deleting users public keys

        Returns True if successfully changed the authorized files and False if
        not (status stays dirty).  If no change attempted, return None.
        """
        mach = self.machine
        if mach.is_down or not self.is_dirty:
            # No update required (either impossible or not needed)
            return None
        env.abort_on_prompts = True
        env.key_filename = os.path.join(KEYS_DIR, 'application')
        env.host_string = "%s@%s:%d" % (self.username,
                                        (mach.ip or mach.hostname),
                                        mach.port)    
        try:
            run('echo "%s" > ~/.ssh/authorized_keys' % "\n".join(
                self.get_authorized_keys()))
            self.is_dirty = False
            self.save()
            return True
        except SystemExit:
            return False

class Client(models.Model):
    nickname = models.CharField(max_length=256)
    description = models.TextField()
    def __unicode__(self):
        return self.nickname

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            UserProfile.objects.create(user=instance)
        except DatabaseError: # Creating fresh db from manage.py
            pass

post_save.connect(create_user_profile, sender=User)


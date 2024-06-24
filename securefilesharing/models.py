from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# profile
class Profile(models.Model):
    auth_user = models.OneToOneField(User, on_delete=models.CASCADE, null=False, default=None, unique=True, related_name='user_profile')
    is_email_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return str(self.auth_user.username)

    class Meta:
        db_table = "user_profile"
        ordering = ['slug']

class File(models.Model):
    file = models.FileField(upload_to='files/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'file'

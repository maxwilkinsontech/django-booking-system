from django.contrib.auth.models import AbstractUser
from django.db import models

from sites.models import Site


class User(AbstractUser):
    """
    Customer User model.
    """

    site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Site this user can manage',
    )
    is_manager = models.BooleanField(
        default=False,
        help_text='Managers have the ability to manage all sites',
    )

    def __str__(self):
        return self.username

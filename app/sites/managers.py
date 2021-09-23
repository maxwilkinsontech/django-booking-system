from django.db import models


class SiteManager(models.Manager):
    """
    Manager for Site model.
    """

    def get_sites(self, user):
        queryset = super().get_queryset()

        if not user.is_manager:
            queryset = queryset.filter(id=user.site_id)

        return queryset

import uuid

from django.db import models


class User(models.Model):
    uid = models.UUIDField(
        db_index=True,
        editable=False,
        default=uuid.uuid4,
        null=False,
    )

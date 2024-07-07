import uuid

from django.db import models

from bot import constants
from bot.common import model_fields


class Server(models.Model):
    uid = models.UUIDField(
        db_index=True,
        editable=False,
        default=uuid.uuid4,
        null=False,
    )

    vendor_uid = models.CharField(
        max_length=32,
        null=False,
        editable=False,
    )
    vendor = model_fields.StringEnumField(
        enum=constants.ServerVendor,
        default=constants.ServerVendor.DISCORD,
        null=False,
    )

    admin_id = models.CharField(
        max_length=32,
        null=False,
        db_index=True,
        editable=False,
    )
    tier = model_fields.IntEnumField(
        enum=constants.ServerTier,
        default=constants.ServerTier.FREE,
        null=False,
    )
    tier_valid_until = models.DateTimeField(null=True)
    status = model_fields.IntEnumField(
        enum=constants.ServerStatus,
        default=constants.ServerStatus.ACTIVE,
        null=False,
    )
    prefix = models.CharField(max_length=1, null=True)

    created = models.DateTimeField(auto_now_add=True, null=False)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'server'
        indexes = [
            models.Index(fields=['tier', 'tier_valid_until']),
        ]
        constraints = [
            models.UniqueConstraint(name='vendor_unique_idx', fields=['vendor', 'vendor_uid']),
        ]


class ServerIntegrationPostFormat(models.Model):
    uid = models.UUIDField(
        db_index=True,
        editable=False,
        default=uuid.uuid4,
        null=False,
    )

    integration = model_fields.StringEnumField(
        enum=constants.Integration,
        null=False,
        editable=False,
    )
    post_format = models.TextField()

    created = models.DateTimeField(auto_now_add=True, null=False)
    updated = models.DateTimeField(auto_now=True, null=True)

    server = models.ForeignKey(Server, on_delete=models.CASCADE)

    class Meta:
        db_table = 'server_integration_post_format'
        constraints = [
            models.UniqueConstraint(
                name='server_integration_unique_idx',
                fields=['server', 'integration'],
            ),
        ]


class ServerPost(models.Model):
    integration = model_fields.StringEnumField(
        enum=constants.Integration,
        null=False,
        editable=False,
    )
    integration_id = models.CharField(
        max_length=64,
        null=False,
        editable=False,
    )
    integration_index = models.PositiveSmallIntegerField(null=True)

    author_id = models.CharField(
        max_length=32,
        null=False,
        db_index=True,
        editable=False,
    )
    url = models.URLField(
        max_length=2000,
        null=False,
        editable=False,
    )
    content = models.TextField()
    blob = models.BinaryField(max_length=1048576)

    created = models.DateTimeField(auto_now_add=True, null=False)

    server = models.ForeignKey(Server, on_delete=models.CASCADE)

    class Meta:
        db_table = 'server_post'
        indexes = [
            models.Index(fields=['server', 'created']),
        ]
        constraints = [
            models.UniqueConstraint(
                name='integration_unique_idx',
                fields=['integration', 'integration_id', 'integration_index', 'server'],
            ),
            models.UniqueConstraint(name='url_unique_idx', fields=['url', 'server']),
        ]

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

    owner = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        default=None,
    )

    class Meta:
        db_table = 'server'
        indexes = [
            models.Index(fields=['tier', 'tier_valid_until']),
        ]
        constraints = [
            models.UniqueConstraint(name='vendor_unique_idx', fields=['vendor', 'vendor_uid']),
        ]


class ServerMember(models.Model):
    uid = models.UUIDField(
        unique=True,
        editable=False,
        default=uuid.uuid4,
        null=False,
    )

    vendor_uid = models.CharField(
        max_length=32,
        null=False,
        editable=False,
    )
    banned = models.BooleanField(
        null=False,
        default=False,
    )

    created = models.DateTimeField(auto_now_add=True, null=False)
    updated = models.DateTimeField(auto_now=True, null=True)

    server = models.ForeignKey(
        Server,
        related_name='users',
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = 'server_member'
        constraints = [
            models.UniqueConstraint(name='vendor_server_unique_idx', fields=['vendor_uid', 'server']),
        ]


class ServerIntegration(models.Model):
    uid = models.UUIDField(
        unique=True,
        editable=False,
        default=uuid.uuid4,
        null=False,
    )

    integration = model_fields.StringEnumField(
        enum=constants.Integration,
        null=False,
        editable=False,
    )
    post_format = models.TextField(null=True, default=None)
    enabled = models.BooleanField(null=False, default=False)

    created = models.DateTimeField(auto_now_add=True, null=False)
    updated = models.DateTimeField(auto_now=True, null=True)

    server = models.ForeignKey(
        Server,
        related_name='integrations',
        on_delete=models.SET_NULL,
        null=True,
        default=None,
    )

    class Meta:
        db_table = 'server_integration'
        constraints = [
            models.UniqueConstraint(
                name='server_integration_unique_idx',
                fields=['server', 'integration'],
            ),
        ]


class Post(models.Model):
    integration = model_fields.StringEnumField(
        enum=constants.Integration,
        null=False,
        editable=False,
    )
    integration_uid = models.CharField(
        max_length=64,
        null=False,
        editable=False,
    )
    integration_index = models.PositiveSmallIntegerField(null=True)

    author = models.CharField(
        max_length=128,
        null=True,
        default=None,
    )
    description = model_fields.CustomCharField(
        max_length=2000,
        null=True,
        default=None,
        auto_trim=True,
    )
    views = models.BigIntegerField(
        null=True,
        default=None,
    )
    likes = models.BigIntegerField(
        null=True,
        default=None,
    )
    spoiler = models.BooleanField(
        null=False,
        default=False,
    )
    posted_at = models.DateTimeField(
        null=True,
        default=None,
    )
    blob = models.BinaryField(
        max_length=1048576,
        null=True,
        default=None,
    )

    created = models.DateTimeField(auto_now_add=True, null=False)

    class Meta:
        db_table = 'post'
        constraints = [
            models.UniqueConstraint(
                name='post_integration_unique_idx',
                fields=['integration', 'integration_uid', 'integration_index'],
            ),
        ]


class ServerPost(models.Model):
    author_uid = models.CharField(
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

    created = models.DateTimeField(auto_now_add=True, null=False)

    server = models.ForeignKey(
        Server,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
    )

    class Meta:
        db_table = 'server_post'
        indexes = [
            models.Index(fields=['server', 'created']),
        ]

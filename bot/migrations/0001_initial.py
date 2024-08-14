# Generated by Django 5.1 on 2024-08-14 17:08
# flake8: noqa
import uuid

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import bot.common.model_fields
import bot.constants


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                (
                    'is_superuser',
                    models.BooleanField(
                        default=False,
                        help_text='Designates that this user has all permissions without explicitly assigning them.',
                        verbose_name='superuser status',
                    ),
                ),
                (
                    'username',
                    models.CharField(
                        error_messages={'unique': 'A user with that username already exists.'},
                        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
                        max_length=150,
                        unique=True,
                        validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                        verbose_name='username',
                    ),
                ),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                (
                    'is_staff',
                    models.BooleanField(
                        default=False,
                        help_text='Designates whether the user can log into this admin site.',
                        verbose_name='staff status',
                    ),
                ),
                (
                    'is_active',
                    models.BooleanField(
                        default=True,
                        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
                        verbose_name='active',
                    ),
                ),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                (
                    'groups',
                    models.ManyToManyField(
                        blank=True,
                        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                        related_name='user_set',
                        related_query_name='user',
                        to='auth.group',
                        verbose_name='groups',
                    ),
                ),
                (
                    'user_permissions',
                    models.ManyToManyField(
                        blank=True,
                        help_text='Specific permissions for this user.',
                        related_name='user_set',
                        related_query_name='user',
                        to='auth.permission',
                        verbose_name='user permissions',
                    ),
                ),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'integration',
                    bot.common.model_fields.StringEnumField(
                        choices=[
                            ('instagram', 'INSTAGRAM'),
                            ('facebook', 'FACEBOOK'),
                            ('tiktok', 'TIKTOK'),
                            ('reddit', 'REDDIT'),
                            ('twitch', 'TWITCH'),
                            ('twitter', 'TWITTER'),
                            ('youtube', 'YOUTUBE'),
                        ],
                        editable=False,
                        enum=bot.constants.Integration,
                        max_length=9,
                    ),
                ),
                ('integration_uid', models.CharField(editable=False, max_length=64)),
                ('integration_index', models.PositiveSmallIntegerField(null=True)),
                ('author', models.CharField(default=None, max_length=128, null=True)),
                ('description', bot.common.model_fields.CustomCharField(default=None, max_length=2000, null=True)),
                ('views', models.BigIntegerField(default=None, null=True)),
                ('likes', models.BigIntegerField(default=None, null=True)),
                ('spoiler', models.BooleanField(default=False)),
                ('posted_at', models.DateTimeField(default=None, null=True)),
                ('blob', models.BinaryField(default=None, max_length=1048576, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'post',
                'constraints': [
                    models.UniqueConstraint(
                        fields=('integration', 'integration_uid', 'integration_index'),
                        name='post_integration_unique_idx',
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('vendor_uid', models.CharField(editable=False, max_length=32)),
                (
                    'vendor',
                    bot.common.model_fields.StringEnumField(
                        choices=[('discord', 'DISCORD')],
                        default=bot.constants.ServerVendor['DISCORD'],
                        enum=bot.constants.ServerVendor,
                        max_length=7,
                    ),
                ),
                (
                    'tier',
                    bot.common.model_fields.IntEnumField(
                        choices=[(1, 'FREE'), (2, 'STANDARD'), (3, 'PREMIUM'), (4, 'ULTRA')],
                        default=bot.constants.ServerTier['FREE'],
                        enum=bot.constants.ServerTier,
                    ),
                ),
                ('tier_valid_until', models.DateTimeField(null=True)),
                (
                    'status',
                    bot.common.model_fields.IntEnumField(
                        choices=[(1, 'ACTIVE'), (2, 'INACTIVE'), (3, 'BLOCKED')],
                        default=bot.constants.ServerStatus['ACTIVE'],
                        enum=bot.constants.ServerStatus,
                    ),
                ),
                ('prefix', models.CharField(max_length=1, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'db_table': 'server',
                'indexes': [models.Index(fields=['tier', 'tier_valid_until'], name='server_tier_a65449_idx')],
                'constraints': [models.UniqueConstraint(fields=('vendor', 'vendor_uid'), name='vendor_unique_idx')],
            },
        ),
        migrations.CreateModel(
            name='ServerIntegration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                (
                    'integration',
                    bot.common.model_fields.StringEnumField(
                        choices=[
                            ('instagram', 'INSTAGRAM'),
                            ('facebook', 'FACEBOOK'),
                            ('tiktok', 'TIKTOK'),
                            ('reddit', 'REDDIT'),
                            ('twitch', 'TWITCH'),
                            ('twitter', 'TWITTER'),
                            ('youtube', 'YOUTUBE'),
                        ],
                        editable=False,
                        enum=bot.constants.Integration,
                        max_length=9,
                    ),
                ),
                ('post_format', models.TextField(default=None, null=True)),
                ('enabled', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'server',
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='integrations',
                        to='bot.server',
                    ),
                ),
            ],
            options={
                'db_table': 'server_integration',
                'constraints': [
                    models.UniqueConstraint(fields=('server', 'integration'), name='server_integration_unique_idx')
                ],
            },
        ),
        migrations.CreateModel(
            name='ServerMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('vendor_uid', models.CharField(editable=False, max_length=32)),
                ('banned', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                (
                    'server',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name='users', to='bot.server'
                    ),
                ),
            ],
            options={
                'db_table': 'server_member',
                'constraints': [
                    models.UniqueConstraint(fields=('vendor_uid', 'server'), name='vendor_server_unique_idx')
                ],
            },
        ),
        migrations.CreateModel(
            name='ServerPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_uid', models.CharField(db_index=True, editable=False, max_length=32)),
                ('url', models.URLField(editable=False, max_length=2000)),
                ('created', models.DateTimeField(auto_now_add=True)),
                (
                    'post',
                    models.ForeignKey(
                        default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.post'
                    ),
                ),
                (
                    'server',
                    models.ForeignKey(
                        default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bot.server'
                    ),
                ),
            ],
            options={
                'db_table': 'server_post',
                'indexes': [models.Index(fields=['server', 'created'], name='server_post_server__0edfec_idx')],
            },
        ),
    ]

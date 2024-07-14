import http

from django import http as django_http
from django import shortcuts
from django.conf import settings
from rest_framework import decorators
from rest_framework import request
from rest_framework import viewsets

from bot.auth.oauth2.discord import oauth2


class Oauth2ViewSet(viewsets.ViewSet):
    @decorators.action(detail=False, methods=[http.HTTPMethod.GET], url_path='login/')
    def login(self, _: request.Request):
        client = oauth2.DiscordOauth2Auth(config=settings.OAUTH2_CONFIGURATION['discord'])
        return shortcuts.redirect(
            client.generate_uri(
                scope=[
                    "identify",
                    "guilds",
                    "connections",
                    "role_connections.write",
                ]
            )
        )

    @decorators.action(detail=False, methods=[http.HTTPMethod.GET], url_path='redirect/')
    def redirect(self, req: request.Request):
        code = req.query_params.get('code')

        client = oauth2.DiscordOauth2Auth(config=settings.OAUTH2_CONFIGURATION['discord'])
        identity = client.exchange_code(code)

        return django_http.JsonResponse(
            {
                "username": identity.user.username,
                "servers": [server.name for server in identity.servers],
            }
        )

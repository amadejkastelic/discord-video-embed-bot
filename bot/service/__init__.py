from django.conf import settings

if settings.DATABASES.get('default', {}).get('ENGINE') == 'django.db.backends.dummy':
    from bot.service import basic as svc
else:
    from bot.service import service as svc


_service = svc.Service()

for name in dir(_service):
    if not name.startswith('_'):
        globals()[name] = getattr(_service, name)

__all__ = [name for name in dir(_service) if not name.startswith('_')]

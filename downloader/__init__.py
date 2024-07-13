import pydantic_core


old_validate_python = pydantic_core.SchemaValidator.validate_python


def validate(*args, **kwargs):
    if getattr(args[0], 'title') == 'VideoPage':
        try:
            args[1]['itemInfo']['itemStruct']['video']['subtitleInfos'] = []
        except Exception:
            pass

    return old_validate_python(*args, **kwargs)


pydantic_core.SchemaValidator.validate_python = validate

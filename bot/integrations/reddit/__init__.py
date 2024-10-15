import pytubefix


def monkey_patch_red_downloader():
    import sys
    from importlib import abc as importlib_abc
    from importlib import machinery as importlib_machinery

    class ReplaceLoader(importlib_abc.Loader):
        def load_module(self, name):
            sys.modules[name] = pytubefix
            return pytubefix

    class ReplaceFinder(importlib_abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname == 'pytube':
                return importlib_machinery.ModuleSpec(fullname, ReplaceLoader())
            return None

    # Insert the custom finder into sys.meta_path
    sys.meta_path.insert(0, ReplaceFinder())


monkey_patch_red_downloader()

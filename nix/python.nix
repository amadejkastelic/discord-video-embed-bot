{
  pkgs,
  lib,
  pyproject-build-systems,
  pyproject-nix,
  python,
  uv2nix,
}:

let
  workspace = uv2nix.lib.workspace.loadWorkspace {
    workspaceRoot = ../.;
  };

  overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

  pyprojectOverrides =
    final: prev:
    let
      inherit (final) resolveBuildSystem;
      inherit (builtins) mapAttrs;

      buildSystemOverrides = {
        aiofiles.hatchling = [ ];
        aiograpi.setuptools = [ ];
        aiosqlite.flit-core = [ ];
        annotated-types.hatchling = [ ];
        appdirs.setuptools = [ ];
        asgiref.setuptools = [ ];
        asyncpraw.flit-core = [ ];
        asyncprawcore.flit-core = [ ];
        attrs.hatchling = [ ];
        cffi.setuptools = [ ];
        cssselect.setuptools = [ ];
        decorator.setuptools = [ ];
        demjson3.setuptools = [ ];
        django-ipware.setuptools = [ ];
        djangorestframework-simplejwt.setuptools = [ ];
        dnspython.hatchling = [ ];
        future.setuptools = [ ];
        httpx.hatchling = [ ];
        idna.flit-core = [ ];
        libipld.maturin = [ ];
        moviepy.setuptools = [ ];
        pycparser.setuptools = [ ];
        pyee.setuptools = [ ];
        pyotp.setuptools = [ ];
        pyquery.setuptools = [ ];
        pytz.setuptools = [ ];
        pyppeteer.setuptools = [ ];
        regex.setuptools = [ ];
        requests.setuptools = [ ];
        sniffio.setuptools = [ ];
        sqlparse.hatchling = [ ];
        tqdm.setuptools = [ ];
        tzlocal.setuptools = [ ];
        update-checker.setuptools = [ ];
        "24ur-api".setuptools = [ ];
        reddownloader.setuptools = [ ];
        w3lib.setuptools = [ ];
        yt-dlp.hatchling = [ ];
        zstandard.setuptools = [ ];
      };
    in
    mapAttrs (
      name: spec:
      prev.${name}.overrideAttrs (old: {
        nativeBuildInputs = old.nativeBuildInputs ++ resolveBuildSystem spec;
      })
    ) buildSystemOverrides;

  pythonSet = (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope (
    lib.composeManyExtensions [
      pyproject-build-systems.overlays.default
      overlay
      pyprojectOverrides
    ]
  );

  venv = pythonSet.mkVirtualEnv "discord-video-embed-bot-env" workspace.deps.default;

  devVenv = pythonSet.mkVirtualEnv "discord-video-embed-bot-dev-env" {
    "discord-video-embed-bot" = [ "dev" ];
  };
in
{
  inherit venv devVenv;
}

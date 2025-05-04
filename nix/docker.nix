{
  pkgs,
  venv,
  browsers,
}:
pkgs.dockerTools.buildLayeredImage {
  name = "discord-video-embed-bot";
  tag = "latest";
  created = "now";

  maxLayers = 10;

  extraCommands = ''
    mkdir -p ./tmp
    chmod 1777 ./tmp
  '';

  contents = [
    venv
    pkgs.ffmpeg-headless
    pkgs.cacert
    pkgs.coreutils
    pkgs.rename
    pkgs.bash
    browsers

    (pkgs.runCommand "project-files" { } ''
      mkdir -p $out/app/conf
      cp -r ${../manage.py} $out/app/manage.py
      cp -r ${../wsgi.py} $out/app/wsgi.py
      cp -r ${../asgi.py} $out/app/asgi.py
      cp -r ${../conf}/* $out/app/conf/
    '')
  ];

  config = {
    Entrypoint = [
      "${venv}/bin/python"
      "/app/manage.py"
    ];
    Env = [
      "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
      "PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true"
      "PLAYWRIGHT_BROWSERS_PATH=${browsers}"
      "LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib"
      "PYTHONFAULTHANDLER=1"
      "PYTHONUNBUFFERED=1"
      "DJANGO_SETTINGS_MODULE=settings"
      "DJANGO_ALLOW_ASYNC_UNSAFE=true"
      "PYTHONPATH=/app"
    ];
    WorkingDir = "/app";
  };
}

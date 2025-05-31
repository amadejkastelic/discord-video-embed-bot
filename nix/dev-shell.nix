{
  pkgs,
  venv,
  browsers,
}:
pkgs.mkShell {
  packages = [
    venv
    pkgs.uv
    pkgs.python312Packages.playwright
    pkgs.ffmpeg
    pkgs.file
    pkgs.nixfmt-tree
    browsers
  ];

  env = {
    UV_NO_SYNC = true;
    UV_PYTHON_DOWNLOADS = "never";
    UV_PYTHON = "${venv}/bin/python";
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
    PLAYWRIGHT_BROWSERS_PATH = browsers;
    PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = true;
    DJANGO_SETTINGS_MODULE = "settings";
  };

  # Workaround: make vscode's python extension read the .venv
  shellHook = ''
    venv="$(cd $(dirname $(which python)); cd ..; pwd)"
    ln -Tsf "$venv" .venv
  '';
}

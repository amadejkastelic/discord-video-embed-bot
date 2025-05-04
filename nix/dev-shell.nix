{
  pkgs,
  devVenv,
  browsers,
}:
pkgs.mkShell {
  packages = [
    devVenv
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
    UV_PYTHON = "${devVenv}/bin/python";
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
    PLAYWRIGHT_BROWSERS_PATH = browsers;
    PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = true;
    DJANGO_SETTINGS_MODULE = "settings";
  };
}

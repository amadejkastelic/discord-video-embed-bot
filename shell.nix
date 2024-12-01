{pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-unstable") {}}:
pkgs.mkShell {
  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";

  packages = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.python-magic
    playwright
    playwright-driver.browsers
    docker-compose
    poetry
    curl
    jq
    file
    ffmpeg
  ];

  shellHook = ''
    export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
    docker-compose up -d
    poetry install && poetry shell
  '';
}

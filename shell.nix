{pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-unstable") {}}:
pkgs.mkShell {
  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";

  packages = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.playwright
    playwright-driver
    docker-compose
    uv
    curl
    jq
    file
    ffmpeg
  ];

  shellHook = ''
    export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
    uv sync
  '';
}

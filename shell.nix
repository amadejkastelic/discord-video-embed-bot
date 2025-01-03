{pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-unstable") {}}:
pkgs.mkShell {
  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";

  packages = with pkgs; [
    python313
    python313Packages.pip
    python313Packages.python-magic
    python313Packages.playwright
    playwright-driver
    docker-compose
    uv
    curl
    jq
    file
    ffmpeg
    cargo
    rustc
    libffi_3_3
  ];

  shellHook = ''
    export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
    uv sync
  '';
}

{pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-unstable") {}}:
pkgs.mkShellNoCC {
  packages = with pkgs; [
    python312
    python312Packages.pip
    docker-compose
    pipenv
    curl
    jq
  ];
}

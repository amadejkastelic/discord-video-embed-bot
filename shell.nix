{pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-23.11") {}}:
pkgs.mkShellNoCC {
  packages = with pkgs; [
    python3
    pipenv
    curl
    jq
  ];
}

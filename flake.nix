{
  description = "Discord Video Embed Bot using uv2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    flake-parts.url = "github:hercules-ci/flake-parts";

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.uv2nix.follows = "uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };
  };

  outputs =
    {
      nixpkgs,
      flake-parts,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
      ...
    }@inputs:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "aarch64-linux"
        "aarch64-darwin"
        "x86_64-linux"
        "x86_64-darwin"
      ];

      perSystem =
        {
          pkgs,
          system,
          ...
        }:
        let
          inherit (nixpkgs) lib;

          python = pkgs.python312;

          pythonConfig = import ./nix/python.nix {
            inherit
              pkgs
              lib
              pyproject-build-systems
              pyproject-nix
              python
              uv2nix
              ;
          };

          inherit (pythonConfig) venv devVenv;

          browsers = pkgs.playwright.browsers.override {
            withChromium = false;
            withFirefox = false;
            withWebkit = false;
            withFfmpeg = false;
            withChromiumHeadlessShell = true;
          };

          dockerImage = import ./nix/docker.nix {
            inherit pkgs venv browsers;
          };
        in
        {
          formatter = pkgs.nixfmt-tree;

          checks = import ./nix/checks.nix {
            inherit pkgs;
            venv = devVenv;
            nixfmt-tree = pkgs.nixfmt-tree;
          };

          packages = {
            default = venv;
            docker = dockerImage;
          };

          apps.default = {
            type = "app";
            program = "${venv}/bin/manage";
          };

          devShells.default = import ./nix/dev-shell.nix {
            inherit pkgs browsers;
            venv = devVenv;
          };
        };
    };
}

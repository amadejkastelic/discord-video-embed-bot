{
  description = "Discord Video Embed Bot";

  outputs = {
    self,
    nixpkgs,
    ...
  } @ inputs:
    inputs.flake-parts.lib.mkFlake {inherit inputs;} {
      systems = ["aarch64-linux" "aarch64-darwin" "x86_64-linux" "x86_64-darwin"];

      perSystem = {
        pkgs,
        config,
        ...
      }: let
        pythonPkg = pkgs.python312;
      in {
        devShells.default = pkgs.mkShell {
          name = "embed-bot";

          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
          PLAYWRIGHT_BROWSERS_PATH = pkgs.playwright-driver.browsers;
          PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = true;
          UV_PYTHON = "${pythonPkg}/bin/python3";

          packages = with pkgs; [
            (pythonPkg.withPackages (ps: [
              ps.playwright
            ]))
            uv
            playwright-driver
            curl
            jq
            file
            ffmpeg
          ];

          shellHook = ''
            uv sync --dev
          '';
        };
      };
    };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };

    flake-compat = {
      url = "github:edolstra/flake-compat";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
}

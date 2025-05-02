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

    # Needed for nix-shell until https://github.com/arrterian/nix-env-selector/pull/97 is merged
    flake-compat.url = "github:edolstra/flake-compat";

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.uv2nix.follows = "uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };
  };

  outputs = {
    nixpkgs,
    flake-parts,
    uv2nix,
    pyproject-nix,
    pyproject-build-systems,
    ...
  } @ inputs:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = ["aarch64-linux" "aarch64-darwin" "x86_64-linux" "x86_64-darwin"];

      perSystem = {
        pkgs,
        system,
        ...
      }: let
        inherit (nixpkgs) lib;

        python = pkgs.python312;
        workspace = uv2nix.lib.workspace.loadWorkspace {workspaceRoot = ./.;};

        overlay = workspace.mkPyprojectOverlay {sourcePreference = "wheel";};

        pyprojectOverrides = final: prev:
        # Implement build fixups here.
        let
          inherit (final) resolveBuildSystem;
          inherit (builtins) mapAttrs;

          buildSystemOverrides = {
            aiofiles.hatchling = [];
            aiograpi.setuptools = [];
            aiosqlite.flit-core = [];
            annotated-types.hatchling = [];
            appdirs.setuptools = [];
            asgiref.setuptools = [];
            asyncpraw.flit-core = [];
            asyncprawcore.flit-core = [];
            attrs.hatchling = [];
            cffi.setuptools = [];
            cssselect.setuptools = [];
            decorator.setuptools = [];
            demjson3.setuptools = [];
            django-ipware.setuptools = [];
            djangorestframework-simplejwt.setuptools = [];
            dnspython.hatchling = [];
            future.setuptools = [];
            httpx.hatchling = [];
            idna.flit-core = [];
            libipld.maturin = [];
            moviepy.setuptools = [];
            pycparser.setuptools = [];
            pyee.setuptools = [];
            pyotp.setuptools = [];
            pyquery.setuptools = [];
            pytz.setuptools = [];
            pyppeteer.setuptools = [];
            regex.setuptools = [];
            requests.setuptools = [];
            sniffio.setuptools = [];
            sqlparse.hatchling = [];
            tqdm.setuptools = [];
            tzlocal.setuptools = [];
            update-checker.setuptools = [];
            "24ur-api".setuptools = [];
            reddownloader.setuptools = [];
            w3lib.setuptools = [];
            yt-dlp.hatchling = [];
            zstandard.setuptools = [];
          };
        in
          mapAttrs (
            name: spec:
              prev.${name}.overrideAttrs (old: {
                nativeBuildInputs = old.nativeBuildInputs ++ resolveBuildSystem spec;
              })
          )
          buildSystemOverrides;

        pythonSet = (pkgs.callPackage pyproject-nix.build.packages {inherit python;}).overrideScope (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
            pyprojectOverrides
          ]
        );

        venv = pythonSet.mkVirtualEnv "discord-video-embed-bot-env" workspace.deps.default;

        devVenv = pythonSet.mkVirtualEnv "discord-video-embed-bot-dev-env" {
          "discord-video-embed-bot" = ["dev"];
        };

        browsers = pkgs.playwright.browsers.overrideAttrs {
          withChromium = false;
          withFirefox = false;
          withWebkit = false;
          withFfmpeg = true;
          withChromiumHeadlessShell = true;
        };

        dockerImage = pkgs.dockerTools.buildImage {
          name = "discord-video-embed-bot";
          tag = "latest";
          created = "now";

          # Tmp dir is needed for playwright
          runAsRoot = ''
            mkdir -p /tmp
          '';

          # Copy the Python virtual environment and other required tools
          copyToRoot = pkgs.buildEnv {
            name = "image-root";
            paths = [
              venv
              pkgs.ffmpeg
              pkgs.file
              pkgs.bash
              pkgs.coreutils
              pkgs.cacert
              browsers
              (pkgs.runCommand "project-files" {} ''
                mkdir -p $out/app/conf
                cp -r ${./manage.py} $out/app/manage.py
                cp -r ${./wsgi.py} $out/app/wsgi.py
                cp -r ${./asgi.py} $out/app/asgi.py
                cp -r ${./conf/settings_base.py} $out/app/conf/settings_base.py
              '')
            ];
            pathsToLink = ["/bin" "/lib" "/app"];
          };

          # Configure environment variables
          config = {
            Entrypoint = ["${venv}/bin/python" "/app/manage.py"];
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
        };
      in {
        packages = {
          default = venv;
          docker = dockerImage;
        };

        apps.default = {
          type = "app";
          program = "${venv}/bin/manage";
        };

        devShells.default = pkgs.mkShell {
          packages = [
            devVenv
            pkgs.uv
            pkgs.python312Packages.playwright
            pkgs.ffmpeg
            pkgs.file
            browsers
          ];

          LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
          PLAYWRIGHT_BROWSERS_PATH = browsers;
          PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = true;
        };
      };
    };
}

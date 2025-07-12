{
  pkgs,
  browsers,
  pyproject-nix,
  pythonSet,
  workspace,
}:
let
  inherit (pkgs.callPackages pyproject-nix.build.util { }) mkApplication;

  app = mkApplication {
    venv = pythonSet.mkVirtualEnv "discord-video-embed-bot-env" workspace.deps.default;
    package = pythonSet.discord-video-embed-bot;
  };
in
pkgs.stdenv.mkDerivation {
  name = "discord-video-embed-bot";

  src = ../.;

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  buildInputs = [
    pkgs.ffmpeg-headless
    browsers
  ];

  installPhase = ''
    mkdir -p $out/bin
    ln -s ${app}/bin/* $out/bin/

    wrapProgram $out/bin/manage \
      --set LD_LIBRARY_PATH "${pkgs.stdenv.cc.cc.lib}/lib" \
      --set PYTHONFAULTHANDLER "1" \
      --set PYTHONUNBUFFERED "1" \
      --set PLAYWRIGHT_BROWSERS_PATH "${browsers}" \
      --set PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS "true" \
      --set DJANGO_ALLOW_ASYNC_UNSAFE "true" \
      --set DJANGO_SETTINGS_MODULE "bot.settings" \
      --prefix PATH : "${pkgs.ffmpeg-headless}/bin:$out/bin"
  '';
}

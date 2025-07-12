{
  pkgs,
  lib,
  module,
  ...
}:

let
  testUserKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIN7DVOB0DJ1x6G9WetQGxzKhj2TgH8DitfTf2xof/Ep amadejkastelic7@gmail.com";

  baseBotConfig =
    { pkgs, ... }:
    {
      imports = [ module ];

      fileSystems."/" = {
        device = "none";
        fsType = "tmpfs";
        options = [ "mode=755" ];
      };

      boot.loader.grub.devices = [ "nodev" ];

      users.users.discordbot.group = "discordbot";
      users.groups.discordbot = { };

      users.users.root = {
        openssh.authorizedKeys.keys = [ testUserKey ];
      };

      services.openssh = {
        enable = true;
        settings.PasswordAuthentication = true;
        settings.PermitRootLogin = "yes";
      };

      virtualisation.memorySize = 4096;

      system.stateVersion = "25.11";
    };

in
pkgs.nixosTest {
  name = "discord-video-embed-bot-test";

  nodes = {
    bot =
      { pkgs, ... }:
      lib.recursiveUpdate (baseBotConfig { inherit pkgs; }) {
        virtualisation.forwardPorts = [
          {
            from = "host";
            host.port = 2222;
            guest.port = 22;
          }
        ];
        discordVideoEmbedBot = {
          enable = true;
          integrationSettings = {
            tiktok.enabled = true;
          };
          db.enable = true;
          cache.enable = true;
        };
      };

    botStandalone =
      { pkgs, ... }:
      lib.recursiveUpdate (baseBotConfig { inherit pkgs; }) {
        virtualisation.forwardPorts = [
          {
            from = "host";
            host.port = 2223;
            guest.port = 22;
          }
        ];
        discordVideoEmbedBot = {
          enable = true;
          integrationSettings = {
            tiktok.enabled = true;
          };
          db.enable = false;
          cache.enable = false;
        };
      };
  };

  testScript = ''
    bot.start()
    bot.wait_for_unit("discord-video-embed-bot.service")
    bot.succeed("systemctl is-active discord-video-embed-bot.service")
  '';
}

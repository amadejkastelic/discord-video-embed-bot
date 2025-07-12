{
  description = "Test system for discord-video-embed-bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    discord-video-embed-bot = {
      url = "..";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      discord-video-embed-bot,
      ...
    }:
    {
      nixosConfigurations.test = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux"; # or your architecture
        modules = [
          discord-video-embed-bot.nixosModules.discord-video-embed-bot
          (
            { ... }:
            {
              # Essential system config for VM/test
              fileSystems."/" = {
                device = "none";
                fsType = "tmpfs";
                options = [ "mode=755" ];
              };

              boot.loader.grub.devices = [ "nodev" ];

              users.users.discordbot.group = "discordbot";
              users.groups.discordbot = { };

              users.users.root = {
                password = "root";
              };

              users.users.test = {
                isNormalUser = true;
                initialPassword = "test";
                home = "/home/test";
                description = "Test User";
                extraGroups = [
                  "wheel"
                  "networkmanager"
                ];
              };

              system.stateVersion = "25.11";

              # Your module config
              discordVideoEmbedBot = {
                enable = true;
                # postgresql.enable = true;
                # memcached.enable = true;
              };
            }
          )
        ];
      };
    };
}

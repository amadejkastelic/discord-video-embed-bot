{
  lib,
  pkgs,
  config,
  package ? null,
  ...
}:
{
  options.discordVideoEmbedBot = {
    enable = lib.mkEnableOption "Enable the Discord Video Embed Bot service";
    package = lib.mkOption {
      type = lib.types.package;
      default = package;
      description = "Package for the Discord Video Embed Bot";
    };
    settingsPath = lib.mkOption {
      type = lib.types.path;
      default = "/etc/discord-video-embed-bot/settings.py";
      description = "Path to the settings file for the Discord Video Embed Bot";
    };
    user = lib.mkOption {
      type = lib.types.str;
      default = "discordbot";
      description = "User under which the Discord Video Embed Bot service runs";
    };
    environment = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      default = { };
      description = "Environment variables for the Discord Video Embed Bot service";
    };
    workingDirectory = lib.mkOption {
      type = lib.types.path;
      default = "/var/lib/discord-video-embed-bot";
      description = "Working directory for the Discord Video Embed Bot service";
    };
    postgresql = {
      enable = lib.mkEnableOption "Enable PostgreSQL for the bot";
      package = lib.mkOption {
        type = lib.types.package;
        default = pkgs.postgresql_16;
        description = "PostgreSQL package to use for the Discord Video Embed Bot";
      };
      initialDatabase = lib.mkOption {
        type = lib.types.str;
        default = "bot";
        description = "Initial database name";
      };
    };
    memcached = {
      enable = lib.mkEnableOption "Enable Memcached for the bot";
      listen = lib.mkOption {
        type = lib.types.str;
        default = "127.0.0.1";
        description = "Address to listen on";
      };
      port = lib.mkOption {
        type = lib.types.int;
        default = 11211;
        description = "Port for Memcached";
      };
    };
  };

  config = lib.mkIf config.discordVideoEmbedBot.enable ({
    users.users.${config.discordVideoEmbedBot.user} = {
      isSystemUser = true;
      home = config.discordVideoEmbedBot.workingDirectory;
      createHome = true;
    };

    systemd.services.discord-video-embed-bot = {
      description = "Discord Video Embed Bot";
      after =
        [ "network.target" ]
        ++ lib.optional config.discordVideoEmbedBot.postgresql.enable "postgresql.service"
        ++ lib.optional config.discordVideoEmbedBot.memcached.enable "memcached.service";
      wantedBy = [ "multi-user.target" ];
      preStart = ''
        ${config.discordVideoEmbedBot.package}/bin/python manage.py migrate
      '';
      serviceConfig = {
        User = config.discordVideoEmbedBot.user;
        WorkingDirectory = config.discordVideoEmbedBot.workingDirectory;
        ExecStart = ''
          ${config.discordVideoEmbedBot.package}/bin/python manage.py discord_bot"
        '';
        /*
          Environment =
          lib.concatStringsSep " " (
            lib.mapAttrsToList (k: v: "${k}=${v}") config.discordVideoEmbedBot.environment
          )
          + "DJANGO_SETTINGS_MODULE=${config.discordVideoEmbedBot.settingsPath}";
        */
        Restart = "always";
      };
      /*
        environment = config.discord-video-embed-bot.environment // {
          DJANGO_SETTINGS_MODULE = config.discordVideoEmbedBot.settingsPath;
        };
      */
    };

    services.postgresql = lib.mkIf config.discordVideoEmbedBot.postgresql.enable {
      enable = true;
      package = config.discordVideoEmbedBot.postgresql.package;
      ensureDatabases = config.discordVideoEmbedBot.postgresql.initialDatabase;
      ensureUsers = [
        {
          name = config.discordVideoEmbedBot.postgresql.initialUser;
          ensureDBOwnership = true;
        }
      ];
    };

    # Enable Memcached if requested
    services.memcached = lib.mkIf config.discordVideoEmbedBot.memcached.enable {
      enable = true;
      listen = config.discordVideoEmbedBot.memcached.listen;
      port = config.discordVideoEmbedBot.memcached.port;
    };
  });
}

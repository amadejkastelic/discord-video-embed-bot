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
    db = {
      enable = lib.mkEnableOption "Enable PostgreSQL for the bot";
      package = lib.mkOption {
        type = lib.types.package;
        default = pkgs.postgresql_16;
        description = "PostgreSQL package to use for the Discord Video Embed Bot";
      };
      port = lib.mkOption {
        type = lib.types.int;
        default = 5432;
        description = "Port for PostgreSQL";
      };
      initialDatabase = lib.mkOption {
        type = lib.types.str;
        default = "bot";
        description = "Initial database name";
      };
    };
    cache = {
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
    };

    systemd.services.discord-video-embed-bot = {
      description = "Discord Video Embed Bot";
      after =
        [ "network.target" ]
        ++ lib.optional config.discordVideoEmbedBot.db.enable "postgresql.service"
        ++ lib.optional config.discordVideoEmbedBot.cache.enable "memcached.service";
      wantedBy = [ "multi-user.target" ];
      preStart = ''
        ${config.discordVideoEmbedBot.package}/bin/manage migrate
      '';
      serviceConfig = {
        User = config.discordVideoEmbedBot.user;
        ExecStart = ''
          ${config.discordVideoEmbedBot.package}/bin/manage discord_bot
        '';
        Restart = "always";
      };
      environment = config.discordVideoEmbedBot.environment // {
        DJANGO_DB_NAME = config.discordVideoEmbedBot.db.initialDatabase;
        DJANGO_DB_USER = config.discordVideoEmbedBot.db.initialDatabase;
        DJANGO_DB_PASSWORD = config.discordVideoEmbedBot.db.initialDatabase;
        DJANGO_DB_PORT = toString config.discordVideoEmbedBot.db.port;

        DJANGO_CACHE_LOCATION = "localhost:${toString config.discordVideoEmbedBot.cache.port}";
      };
    };

    services.postgresql = lib.mkIf config.discordVideoEmbedBot.db.enable {
      enable = true;
      package = config.discordVideoEmbedBot.db.package;
      ensureDatabases = [ config.discordVideoEmbedBot.db.initialDatabase ];
      ensureUsers = [
        {
          name = config.discordVideoEmbedBot.db.initialDatabase;
          ensureDBOwnership = true;
          ensureClauses.login = true;
        }
      ];
      initialScript = pkgs.writeText "init.sql" ''
        DO
        $do$
        BEGIN
          IF NOT EXISTS (
            SELECT FROM pg_catalog.pg_roles WHERE rolname = '${config.discordVideoEmbedBot.db.initialDatabase}'
          ) THEN
            CREATE ROLE "${config.discordVideoEmbedBot.db.initialDatabase}" LOGIN PASSWORD '${config.discordVideoEmbedBot.db.initialDatabase}';
          ELSE
            ALTER ROLE "${config.discordVideoEmbedBot.db.initialDatabase}" WITH PASSWORD '${config.discordVideoEmbedBot.db.initialDatabase}';
          END IF;
        END
        $do$;
      '';
    };

    services.memcached = lib.mkIf config.discordVideoEmbedBot.cache.enable {
      enable = true;
      listen = config.discordVideoEmbedBot.cache.listen;
      port = config.discordVideoEmbedBot.cache.port;
    };
  });
}

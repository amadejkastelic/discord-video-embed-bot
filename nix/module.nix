{
  lib,
  pkgs,
  config,
  package ? null,
  ...
}:
{
  options.services.discordVideoEmbedBot = {
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
    integrationSettings = lib.mkOption {
      type = lib.types.attrs;
      default = { };
      description = "Integration settings for the Discord Video Embed Bot";
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
        default = "localhost";
        description = "Address to listen on";
      };
      port = lib.mkOption {
        type = lib.types.int;
        default = 11211;
        description = "Port for Memcached";
      };
    };
  };

  config = lib.mkIf config.services.discordVideoEmbedBot.enable ({
    users.users.${config.services.discordVideoEmbedBot.user} = {
      isSystemUser = true;
    };

    systemd.services.discord-video-embed-bot = {
      description = "Discord Video Embed Bot";
      after =
        [ "network.target" ]
        ++ lib.optional config.services.discordVideoEmbedBot.db.enable "postgresql.service"
        ++ lib.optional config.services.discordVideoEmbedBot.cache.enable "memcached.service";
      wantedBy = [ "multi-user.target" ];
      preStart = lib.mkIf config.services.discordVideoEmbedBot.db.enable ''
        ${config.services.discordVideoEmbedBot.package}/bin/manage migrate
      '';
      serviceConfig = {
        User = config.services.discordVideoEmbedBot.user;
        ExecStart = ''
          ${config.services.discordVideoEmbedBot.package}/bin/manage discord_bot
        '';
        Restart = "always";
      };
      environment = config.services.discordVideoEmbedBot.environment // {
        DJANGO_DB_ENGINE =
          if config.services.discordVideoEmbedBot.db.enable then
            "django.db.backends.postgresql"
          else
            "django.db.backends.dummy";
        DJANGO_DB_NAME = config.services.discordVideoEmbedBot.db.initialDatabase;
        DJANGO_DB_USER = config.services.discordVideoEmbedBot.db.initialDatabase;
        DJANGO_DB_PASSWORD = config.services.discordVideoEmbedBot.db.initialDatabase;
        DJANGO_DB_PORT = toString config.services.discordVideoEmbedBot.db.port;

        DJANGO_CACHE_BACKEND =
          if config.services.discordVideoEmbedBot.cache.enable then
            "django.core.cache.backends.memcached.PyMemcacheCache"
          else
            "django.core.cache.backends.dummy.DummyCache";
        DJANGO_CACHE_LOCATION = "localhost:${toString config.services.discordVideoEmbedBot.cache.port}";

        INTEGRATION_CONFIGURATION_JSON = builtins.toJSON config.services.discordVideoEmbedBot.integrationSettings;
      };
    };

    services.postgresql = lib.mkIf config.services.discordVideoEmbedBot.db.enable {
      enable = true;
      package = config.services.discordVideoEmbedBot.db.package;
      ensureDatabases = [ config.services.discordVideoEmbedBot.db.initialDatabase ];
      ensureUsers = [
        {
          name = config.services.discordVideoEmbedBot.db.initialDatabase;
          ensureDBOwnership = true;
          ensureClauses.login = true;
        }
      ];
      initialScript = pkgs.writeText "init.sql" ''
        DO
        $do$
        BEGIN
          IF NOT EXISTS (
            SELECT FROM pg_catalog.pg_roles WHERE rolname = '${config.services.discordVideoEmbedBot.db.initialDatabase}'
          ) THEN
            CREATE ROLE "${config.services.discordVideoEmbedBot.db.initialDatabase}" LOGIN PASSWORD '${config.services.discordVideoEmbedBot.db.initialDatabase}';
          ELSE
            ALTER ROLE "${config.services.discordVideoEmbedBot.db.initialDatabase}" WITH PASSWORD '${config.services.discordVideoEmbedBot.db.initialDatabase}';
          END IF;
        END
        $do$;
      '';
    };

    services.memcached = lib.mkIf config.services.discordVideoEmbedBot.cache.enable {
      enable = true;
      listen = config.services.discordVideoEmbedBot.cache.listen;
      port = config.services.discordVideoEmbedBot.cache.port;
    };
  });
}

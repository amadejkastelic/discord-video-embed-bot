{
  lib,
  pkgs,
  config,
  package ? null,
  ...
}:
let
  cfg = config.services.discordVideoEmbedBot;
in
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
    group = lib.mkOption {
      type = lib.types.str;
      default = cfg.user;
      description = "Group under which the Discord Video Embed Bot service runs";
    };
    environment = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      default = { };
      description = "Environment variables for the Discord Video Embed Bot service";
    };
    environmentFile = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "Path to the environment file for the Discord Video Embed Bot service";
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
        default = pkgs.postgresql;
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

  config = lib.mkIf cfg.enable ({
    users.users.${cfg.user} = {
      name = cfg.user;
      group = cfg.group;
      description = "Discord Video Embed Bot User";
      isSystemUser = true;
    };

    users.groups.${cfg.group} = {
      name = cfg.group;
    };

    systemd.services.discord-video-embed-bot = {
      description = "Discord Video Embed Bot";
      after =
        [ "network.target" ]
        ++ lib.optional cfg.db.enable "postgresql.service"
        ++ lib.optional cfg.cache.enable "memcached.service";
      wantedBy = [ "multi-user.target" ];
      preStart = lib.mkIf cfg.db.enable ''
        ${cfg.package}/bin/manage migrate
      '';
      serviceConfig = {
        User = cfg.user;
        Group = cfg.group;
        ExecStart = ''
          ${cfg.package}/bin/manage discord_bot
        '';
        Restart = "always";
        EnvironmentFile = lib.mkIf (cfg.environmentFile != null) cfg.environmentFile;
      };
      environment = cfg.environment // {
        DJANGO_DB_ENGINE =
          if cfg.db.enable then "django.db.backends.postgresql" else "django.db.backends.dummy";
        DJANGO_DB_NAME = cfg.db.initialDatabase;
        DJANGO_DB_USER = cfg.db.initialDatabase;
        DJANGO_DB_PASSWORD = cfg.db.initialDatabase;
        DJANGO_DB_PORT = toString cfg.db.port;

        DJANGO_CACHE_BACKEND =
          if cfg.cache.enable then
            "django.core.cache.backends.memcached.PyMemcacheCache"
          else
            "django.core.cache.backends.dummy.DummyCache";
        DJANGO_CACHE_LOCATION = "localhost:${toString cfg.cache.port}";

        INTEGRATION_CONFIGURATION_JSON = builtins.toJSON cfg.integrationSettings;
      };
    };

    services.postgresql = lib.mkIf cfg.db.enable {
      enable = true;
      package = cfg.db.package;
      ensureDatabases = [ cfg.db.initialDatabase ];
      ensureUsers = [
        {
          name = cfg.db.initialDatabase;
          ensureDBOwnership = true;
          ensureClauses.login = true;
        }
      ];
      initialScript = pkgs.writeText "init.sql" ''
        DO
        $do$
        BEGIN
          IF NOT EXISTS (
            SELECT FROM pg_catalog.pg_roles WHERE rolname = '${cfg.db.initialDatabase}'
          ) THEN
            CREATE ROLE "${cfg.db.initialDatabase}" LOGIN PASSWORD '${cfg.db.initialDatabase}';
          ELSE
            ALTER ROLE "${cfg.db.initialDatabase}" WITH PASSWORD '${cfg.db.initialDatabase}';
          END IF;
        END
        $do$;
      '';
    };

    services.memcached = lib.mkIf cfg.cache.enable {
      enable = true;
      listen = cfg.cache.listen;
      port = cfg.cache.port;
    };
  });
}

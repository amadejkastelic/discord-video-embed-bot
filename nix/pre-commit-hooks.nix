{ inputs, ... }:
{
  imports = [ inputs.pre-commit-hooks.flakeModule ];

  perSystem.pre-commit = {

    settings = {
      src = ../.;
      hooks = {
        nixfmt-rfc-style.enable = true;
        ruff.enable = true;
      };
    };
  };
}

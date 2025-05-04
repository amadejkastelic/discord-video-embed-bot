{
  pkgs,
  devVenv,
  nixfmt-tree,
}:
let
  src = ./..;

  runCheck =
    name: command:
    pkgs.runCommand name
      {
        nativeBuildInputs = [
          devVenv
          nixfmt-tree
        ];
        src = src;
      }
      ''
        cd ${src}
        export PATH=${devVenv}/bin:$PATH
        export DJANGO_SETTINGS_MODULE=conf.settings_test
        export TREEFMT_TREE_ROOT=${src}
        ${command}
        touch $out
      '';
in
{
  flake8 = runCheck "flake8" "flake8 ./bot/**/*.py";
  pylint = runCheck "pylint" "pylint ./bot/**/*.py";
  black = runCheck "black-formatting" "black --check --diff ./bot/**/*.py";
  nixfmt = runCheck "nixfmt" "treefmt --ci";
}

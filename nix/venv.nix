{ env }:

{
  venv = env.pythonSet.mkVirtualEnv "discord-video-embed-bot-env" env.workspace.deps.default;

  devVenv = env.pythonSet.mkVirtualEnv "discord-video-embed-bot-dev-env" {
    "discord-video-embed-bot" = [ "dev" ];
  };
}

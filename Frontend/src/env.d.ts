interface EnvConfig {
  navigationBotApiUrl: string;
  lostAndFoundApiUrl: string;
}

interface Window {
  __env: EnvConfig;
}

import bolt from "@slack/bolt";

const botToken = process.env.SLACK_BOT_TOKEN?.trim();
const appToken = process.env.SLACK_APP_TOKEN?.trim();

if (!botToken?.startsWith("xoxb-") || !appToken?.startsWith("xapp-")) {
  console.error(
    "Set SLACK_BOT_TOKEN (xoxb-) and SLACK_APP_TOKEN (xapp-) before starting Slack.",
  );
  process.exit(1);
}

try {
  const app = new bolt.App({
    token: botToken,
    appToken,
    socketMode: true,
    deferInitialization: true,
  });

  await app.init();
  await app.start();
  console.info("Slack Socket Mode started.");
} catch {
  console.error("Slack startup failed. Check the app installation, tokens, and Socket Mode settings.");
  process.exit(1);
}

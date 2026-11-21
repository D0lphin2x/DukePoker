# Instagram event sync setup

This repository can poll the Duke Poker professional Instagram account for new posts. Only captions containing `#DukePokerEvent` are published to the website. The first run stores a checkpoint and does not import older posts.

## Caption format

Add the marker and labeled fields to an event post caption:

```text
#DukePokerEvent
Title: Fall Poker Night
Date: October 14, 2027
Time: 7:00 PM–10:00 PM
Location: Wilkinson 126
Description: Join us for a night of cards, prizes, and community.
RSVP: https://example.com/rsvp
```

`Title` and `Date` are required. `Time`, `Location`, `Description`, and `RSVP` are optional. If no `RSVP` is supplied, the site links no signup button. Event photos are copied into the repo when Meta returns a supported image URL; otherwise the site uses its existing placeholder.

## Instagram credentials

The Instagram account must be a Business or Creator account. Create a Meta developer app with the Instagram API with Instagram Login, authorize the Duke Poker account for `instagram_business_basic`, and retrieve the Instagram user ID and an access token. Meta's API reads media owned by the connected professional account; it is not a public-feed watcher for arbitrary accounts.

In GitHub, open **D0lphin2x/DukePoker → Settings → Secrets and variables → Actions** and add:

- Repository secret `INSTAGRAM_USER_ID`
- Repository secret `INSTAGRAM_ACCESS_TOKEN`
- Repository variable `INSTAGRAM_SYNC_ENABLED` with value `true`

Never paste the access token into chat or commit it to the repository. Meta access tokens can expire (long-lived user tokens are typically valid for about 60 days) or be revoked; if the sync reports an authentication error, generate and replace the secret with a fresh token.

## Deployment behavior

The workflow checks for new posts every 15 minutes and can also be started manually from the GitHub Actions tab. For each new marked post, it updates `duke-poker-website/instagram_events.json`, commits the event to `main`, and waits for the title to appear on `https://dukepoker.org/announcements`. Render's existing GitHub auto-deploy then publishes it. GitHub scheduled jobs can be delayed during high load, so this is periodic polling rather than an instant notification.

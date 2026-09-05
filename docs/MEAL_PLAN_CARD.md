# Meal Plan Card

The Meal Plan Card shows this week's dinners from [Shoplist](https://shoplist.wtm.se/meal-plan) via a private JSON feed.

## Features

- 🍽 Protein emoji, recipe title, and day (Today / Tomorrow / Mon…)
- 🎨 Same look as the Calendar card (first meal bold, later meals dim)
- 🔄 Auto-updates every 5 minutes (configurable)
- 📍 Positioned at TOP_RIGHT by default
- Cooked meals are struck through and sorted last

## Configuration

Add to your `.env` file:

```bash
ENABLE_MEAL_PLAN=true

# Copied from Shoplist → Sharing → Mirror feed
MEAL_PLAN_FEED_URL=https://<project>.supabase.co/functions/v1/meal-plan-feed?token=<uuid>

# Public Shoplist anon key (the function gateway requires it; the token is the secret)
MEAL_PLAN_ANON_KEY=

# Maximum dinners to show (optional, default: 6)
MEAL_PLAN_MAX_ITEMS=6

# Seconds between refreshes (optional, default: 300). The feed 429s below 5s.
MEAL_PLAN_UPDATE_INTERVAL=300
```

## Getting the feed URL

1. Open Shoplist → **Sharing** (Settings, or the members icon)
2. Under **Mirror feed**, create a URL and copy it
3. Paste it as `MEAL_PLAN_FEED_URL`
4. Set `MEAL_PLAN_ANON_KEY` to the same public anon key the Shoplist web app uses (`VITE_SUPABASE_ANON_KEY`)

⚠️ **Important**: Anyone with the feed URL can read this week's dinners. Treat it like a password. Create a new URL or turn the feed off in Shoplist to invalidate the old one.

The Pi does **not** log in to Shoplist. Auth is the unguessable token plus the public anon key.

## Display Format

```
🍽  This week

🐔  Chicken curry
   Today

🐟  Fish stew
   Tomorrow

🌱  Lentil soup
   Wed
```

- **First uncooked meal** in white/bold
- **Remaining meals** dimmed
- **Cooked meals** struck through, after uncooked ones
- **Unscheduled** recipes (no day) have no subtitle and sort after dated meals

## Customization

You can customize the card in [meal_plan.py](../smart_mirror/plugins/meal_plan.py):

- **Position**: Change `CardPosition.TOP_RIGHT`
- **Update interval**: `MEAL_PLAN_UPDATE_INTERVAL` in `.env` (seconds, minimum 5)
- **Icons**: `PROTEIN_ICONS` (keep in sync with Shoplist)

## Troubleshooting

### No meals showing

- Confirm the feed is deployed: `supabase functions deploy meal-plan-feed --no-verify-jwt`
- Confirm the migration `015_meal_plan_feed.sql` is applied
- Check `MEAL_PLAN_FEED_URL` includes `?token=`
- Check `MEAL_PLAN_ANON_KEY` is set (gateway 401 without it)
- Rotate the feed in Shoplist if the token was revoked

### HTTP 429

The feed allows one request per token every 5 seconds. The card polls every 5 minutes, so this should not appear in normal use.

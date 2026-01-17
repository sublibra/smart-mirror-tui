# Transport Card Configuration

The Transport Card displays upcoming departures from a Swedish transport station using the **Trafiklab Realtime API**.

## Setup

### 1. Get API Keys

- Sign up at [trafiklab.se](https://www.trafiklab.se)
- Request access to: **Trafiklab Realtime API** (for live departures)
- Generate an API key

### 2. Find Your Station ID

Use the helper script to find your station's correct ID:

```bash
python lookup_station.py "Stehag" your-api-key
```

The script will output:
```
Found 1 station group(s):

  ID: 740000952
  Name: Stehag station
  Modes: ['BUS', 'TRAIN']

To use 'Stehag station', add to .env:
  TRANSPORT_STATION_ID=740000952
```

Or manually look it up:
```bash
https://realtime-api.trafiklab.se/v1/stops/name/Stehag?key=your-api-key
```

The response will contain `stop_groups` array. Use the `id` from the first matching group.

### 3. Configure .env

```env
TRANSPORT_API_KEY=your-trafiklab-api-key
TRANSPORT_STATION_ID=740013049
TRANSPORT_UPDATE_INTERVAL=120
TRANSPORT_DELAY_THRESHOLD=120
TRANSPORT_TIME_WINDOW=60
TRANSPORT_MAX_DEPARTURES=6
```

**Parameters:**
- `TRANSPORT_API_KEY` - Your Trafiklab API key (required)
- `TRANSPORT_STATION_ID` - Station ID from the lookup (required)
- `TRANSPORT_UPDATE_INTERVAL` - How often to fetch data in seconds (default: 120)
- `TRANSPORT_DELAY_THRESHOLD` - Minimum delay in seconds to show warning (default: 120)
- `TRANSPORT_TIME_WINDOW` - Unused (kept for compatibility)
- `TRANSPORT_MAX_DEPARTURES` - How many departures to display (default: 6)

## Features

✅ **Live Updates** - Continuously updated, cached for 60 seconds  
✅ **Delay Warnings** - Shows `[WARN +3m]` for delays exceeding threshold  
✅ **Cancellations** - Automatically hides canceled departures  
✅ **Platform Info** - Shows scheduled and realtime platforms (when available)  
✅ **All Operators** - Works with all Swedish transport operators  

## Display Format

```
BUS 50 Central - in 8m (10:30)
TRN A North - in 12m (10:34) [WARN +3m]
MET 19 Hagsätra - now (10:22)
```

Format: `MODE LINE DESTINATION - TIME [DELAY_WARNING]`

## Troubleshooting

**404 Error**: Station ID not found. Use the lookup script to find the correct ID from `stop_groups[].id`.  
**403 Error**: API key doesn't have access to Trafiklab Realtime API.  
**No data shown**: Check that the station ID exists and has departures in the next 60 minutes.

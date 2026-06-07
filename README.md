# NWS Alerts for Home Assistant

![CI](https://github.com/tannerprice/ha-nws-alerts/actions/workflows/ci.yml/badge.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue.svg)
![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)
![License](https://img.shields.io/github/license/tannerprice/nws-alerts)
![Python](https://img.shields.io/badge/Python-3.13-blue)

A Home Assistant custom integration that monitors active weather alerts from the National Weather Service (NWS) API and exposes them as Home Assistant entities and events.

This integration is designed for weather enthusiasts, storm spotters, emergency preparedness automations, weather radios, and anyone who wants fine-grained control over NWS alert notifications.

---

## Features

- Fetches active alerts directly from the National Weather Service API
- Supports NWS alert filtering options
- Configurable entirely through the Home Assistant UI
- Exposes active alert count as a Home Assistant sensor
- Fires Home Assistant events when alerts are:
  - Issued
  - Updated
  - Cancelled
- Prevents duplicate triggers for the same alert revision
- Supports multiple independently configured integrations
- HACS compatible
- Fully typed with BasedPyright
- Automated testing and CI/CD
- Automated releases and changelog generation

---

## Example Use Cases

### Tornado Warning Notifications

Receive push notifications when a Tornado Warning is:

- Issued
- Updated
- Cancelled

### Weather Radio Automation

Trigger:

- Sirens
- Smart lights
- TTS announcements
- ESPHome weather indicators

based on incoming NWS alerts.

### Storm Monitoring Dashboard

Display:

- Active alert count
- Alert headlines
- Severity information

inside Home Assistant dashboards.

### Emergency Preparedness

Automatically:

- Turn on emergency lighting
- Pause irrigation systems
- Trigger weather radios
- Activate backup power workflows

during severe weather events.

---

## Installation

### HACS (Recommended)

1. Open HACS.
2. Navigate to **Integrations**.
3. Click **Custom Repositories**.
4. Add this repository URL.
5. Select **Integration**.
6. Click **Add**.
7. Install **NWS Alerts**.
8. Restart Home Assistant.

### Manual Installation

Copy the integration into your Home Assistant configuration directory:

```text
config/
└── custom_components/
    └── nws_alerts/
```

Restart Home Assistant.

---

## Configuration

Navigate to:

```text
Settings → Devices & Services → Add Integration
```

Search for:

```text
NWS Alerts
```

and configure the desired filters.

### Required Configuration

| Option | Description |
|----------|----------|
| User-Agent | Contact string required by the NWS API |
| Scan Interval | Polling interval in seconds |

#### Example User-Agent

```text
HomeAssistant-NWSAlerts/1.0 your-email@example.com
```

Replace the email address with a valid contact method.

---

## Optional Filters

| Filter | Example |
|----------|----------|
| status | Actual |
| message_type | Alert |
| event | Tornado Warning |
| code | TOR |
| area | TX |
| point | 32.7767,-96.7970 |
| region | Southern |
| region_type | land |
| zone | TXC113 |
| urgency | Immediate |
| severity | Extreme |
| certainty | Observed |
| limit | 50 |

### Example Configurations

#### All Texas Alerts

```yaml
area: TX
```

#### Tornado Warnings

```yaml
event: Tornado Warning
```

#### Severe Weather

```yaml
severity: Severe
urgency: Immediate
```

#### Dallas County

```yaml
zone: TXC113
```

---

## Entities

### Alert Count Sensor

Example:

```text
sensor.nws_alerts
```

State:

```text
4
```

Meaning:

```text
4 active alerts match the configured filters.
```

### Sensor Attributes

| Attribute | Description |
|------------|-------------|
| alerts | List of active alerts |
| url | Generated NWS API URL |

Example:

```yaml
alerts:
  - event: Tornado Warning
    severity: Extreme
    urgency: Immediate
    certainty: Observed
    headline: Tornado Warning issued for Dallas County

url: https://api.weather.gov/alerts/active?area=TX
```

---

## Home Assistant Events

The integration emits events whenever an alert changes.

### Generic Alert Event

```text
nws_alerts_alert
```

Fires for all alert activity.

### Alert Issued

```text
nws_alerts_alert_issued
```

Fires when a new alert is issued.

### Alert Updated

```text
nws_alerts_alert_updated
```

Fires when an alert is updated.

### Alert Cancelled

```text
nws_alerts_alert_cancelled
```

Fires when an alert is cancelled.

---

## Event Payload

Example:

```yaml
id: abc123

event: Tornado Warning
headline: Tornado Warning issued for Dallas County

severity: Extreme
urgency: Immediate
certainty: Observed

status: Actual
message_type: Update

sent: 2026-06-07T12:00:00-05:00
updated: 2026-06-07T12:10:00-05:00
expires: 2026-06-07T12:45:00-05:00

is_new: false
is_update: true
is_cancel: false
```

---

## Automation Examples

### Notify When a Tornado Warning Is Issued

```yaml
alias: Tornado Warning Issued

trigger:
  - platform: event
    event_type: nws_alerts_alert_issued

condition:
  - condition: template
    value_template: >
      {{ trigger.event.data.event == 'Tornado Warning' }}

action:
  - service: notify.mobile_app_phone
    data:
      title: Tornado Warning
      message: >
        {{ trigger.event.data.headline }}
```

### Notify When a Warning Is Updated

```yaml
alias: Warning Updated

trigger:
  - platform: event
    event_type: nws_alerts_alert_updated

action:
  - service: notify.mobile_app_phone
    data:
      title: Alert Updated
      message: >
        {{ trigger.event.data.headline }}
```

### Notify When a Warning Is Cancelled

```yaml
alias: Warning Cancelled

trigger:
  - platform: event
    event_type: nws_alerts_alert_cancelled

action:
  - service: notify.mobile_app_phone
    data:
      title: Alert Cancelled
      message: >
        {{ trigger.event.data.headline }}
```

---

## Duplicate Prevention

The integration prevents duplicate event triggers.

A unique fingerprint is generated using:

```text
Alert ID
Message Type
Sent Timestamp
Updated Timestamp
Expiration Timestamp
```

This guarantees:

- An alert is issued only once
- An update is processed only once
- A cancellation is processed only once
- Polling the same alert repeatedly does not retrigger automations

---

## Startup Behavior

To avoid notification spam after Home Assistant restarts:

- Existing active alerts are loaded during startup
- No events are fired for alerts already active
- Only newly observed alert revisions generate events

This prevents dozens of historical alerts from retriggering automations after a restart.


## Development

### Requirements

- Python 3.13
- uv
- Git

### Install Dependencies

```bash
uv sync --group dev
```

### Run Tests

```bash
uv run pytest
```

### Run Ruff

```bash
uv run ruff check .
```

### Run BasedPyright

```bash
uv run basedpyright .
```

### Run Everything

```bash
uv run ruff check .
uv run basedpyright .
uv run pytest
```

---

## Continuous Integration

Every pull request and push to the main branch runs:

- Ruff
- BasedPyright
- Pytest
- HACS Validation
- Hassfest

All checks must pass before merging.

---

## Versioning

This project follows Conventional Commits and Release Please.

| Prefix | Version Impact |
|----------|----------|
| feat: | Minor |
| fix: | Patch |
| perf: | Patch |
| docs: | No Release |
| chore: | No Release |
| refactor: | No Release |

Examples:

```text
feat: support alert cancellation events
fix: prevent duplicate alert triggers
docs: update README
chore: update dependencies
```

### Breaking Changes

```text
feat!: redesign event payloads
```

or

```text
BREAKING CHANGE: redesigned event payloads
```

results in a major version bump.

---

## Release Process

Releases are fully automated.

### Development Workflow

1. Create a branch
2. Open a pull request
3. Use a Conventional Commit title
4. Merge into main

Example:

```text
feat: add alert expiration tracking
```

### Automatic Release Flow

After changes are merged:

1. Release Please evaluates merged commits
2. A Release PR is generated
3. The Release PR updates:
   - CHANGELOG.md
   - manifest.json version
   - release metadata
4. Merge the Release PR
5. GitHub automatically creates:
   - Git tag
   - GitHub Release
   - Release Notes

---

## Testing

Current test coverage includes:

### Coordinator

- Alert fetching
- URL generation
- Alert parsing
- Event generation
- Duplicate suppression
- Startup behavior
- Update events
- Cancellation events

### Config Flow

- User configuration
- Entry creation

### Sensor

- State synchronization
- Attribute synchronization

---

## Contributing

Contributions are welcome.

Before submitting a pull request:

```bash
uv run ruff check .
uv run basedpyright .
uv run pytest
```

All checks should pass.

Pull request titles should follow Conventional Commit conventions.

Example:

```text
feat: support alert expiration tracking
```

---

## Disclaimer

This integration is not affiliated with or endorsed by:

- National Weather Service (NWS)
- NOAA
- United States Government

Weather alerts should never be your sole source of emergency information. Always maintain multiple methods of receiving critical weather warnings.

---

## License

MIT License

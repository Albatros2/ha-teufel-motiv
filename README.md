# Teufel Motiv Home LAN HA-Integration

Unofficial local LAN integration for Teufel speakers discovered via mDNS service `_teufelstreaming._tcp.local.`

## Quick Add

[![Open your Home Assistant instance and add this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Albatros2&repository=ha-teufel-motiv&category=integration)

[![Open your Home Assistant instance and start setting up this integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=teufel_lan)

## Features

- mDNS discovery (zeroconf)
- Device grouping in Home Assistant (one device with multiple controls)
- Media Player entity with artwork from stream metadata
- Set volume via local API
- Mute/unmute via local API
- Bass and treble EQ controls
- Buttons: Stop and Preset 1-3
- Start TuneIn station by guide ID
- Source selection from play history

## Recommended Dashboard Card

If you want a compact device-like view with sliders, toggle and buttons, add this to a dashboard:

```yaml
type: entities
title: Teufel Speaker
show_header_toggle: false
entities:
	- entity: media_player.teufel_speaker
		name: Player
	- entity: switch.teufel_speaker_mute
		name: Mute
	- entity: number.teufel_speaker_bass
		name: Bass
	- entity: number.teufel_speaker_treble
		name: Treble
	- entity: button.teufel_speaker_stop
		name: Stop
	- entity: button.teufel_speaker_preset_1
		name: Preset 1
	- entity: button.teufel_speaker_preset_2
		name: Preset 2
	- entity: button.teufel_speaker_preset_3
		name: Preset 3
```

Entity IDs may vary depending on your configured name.

## Reverse engineered API paths used

- `/api/setData`
- `/api/getData`
- `/api/getRows`

## Example payloads

Set volume:

```json
{"path":"player:volume","roles":"value","value":{"type":"i32_","i32_":18}}
```

Mute:

```json
{"path":"settings:/mediaPlayer/mute","roles":"value","value":{"type":"bool_","bool_":true}}
```

Bass:

```json
{"path":"settings:/dspc/dspcBass","roles":"value","value":{"type":"i32_","i32_":3}}
```

Treble:

```json
{"path":"settings:/dspc/dspcTreble","roles":"value","value":{"type":"i32_","i32_":2}}
```

Stop:

```json
{"path":"player:player/control","roles":"activate","value":{"control":"stop"}}
```

TuneIn by guide ID:

```json
{"path":"tunein:tuneInRequestByGuideId","roles":"activate","value":{"type":"string_","string_":"e244095389"}}
```

## Installation

1. Copy `custom_components/teufel_lan` into your Home Assistant config directory under `custom_components`.
2. Restart Home Assistant.
3. Add the integration through the UI.

## Notes

This project is unofficial and based on observed LAN traffic.

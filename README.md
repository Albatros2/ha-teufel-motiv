# Teufel LAN Home Assistant Integration

Unofficial local LAN integration for Teufel speakers discovered via mDNS service `_teufelstreaming._tcp.local.`

## Features

- mDNS discovery (zeroconf)
- Media Player entity
- Set volume via local API
- Mute/unmute via local API
- Bass and treble EQ controls
- Stop playback
- Start TuneIn station by guide ID
- Source selection from play history

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

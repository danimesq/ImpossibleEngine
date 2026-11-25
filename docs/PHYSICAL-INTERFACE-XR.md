# Physical Interface & XR System (IPIX)

Status: architecture proposal and compatibility inventory. This document does **not** claim that the listed hardware is already supported by the engine.

## Goals

ImpossibleEngine should expose physical interfaces through a capability-oriented Rust API. Games ask for capabilities (6DoF head pose, articulated hands, locomotion velocity, finger force feedback), not vendor names. Device discovery, transport, vendor protocol decoding, calibration, safety and game-facing actions are separate layers.

The practical target is broad interoperability, not a promise that every product ever made can be controlled. Proprietary devices without a public protocol, SDK, driver or documented transport can be detected at most; full control requires vendor cooperation or a lawful, independently developed adapter.

## Layered architecture

```text
Game / Event Sheet / Rust runtime
              |
      IPIX capability API
              |
   Device registry + profiles
              |
   Provider / protocol adapters
              |
 OpenXR | OpenVR | HID | USB | BLE | Serial | OSC/UDP | vendor SDK
              |
         Physical devices
```

Recommended workspace boundary (future implementation):

- `ipix-core`: device identity, capabilities, timestamps, coordinate spaces, health and error types. No hardware I/O.
- `ipix-registry`: discovery, matching, profiles, hot-plug and permission state.
- `ipix-openxr`: headset, controllers, hand/eye/body tracking and standard haptics.
- `ipix-openvr`: legacy/SteamVR runtime compatibility where OpenXR is unavailable or insufficient.
- `ipix-hid`, `ipix-usb`, `ipix-ble`, `ipix-serial`: transport backends.
- `ipix-locomotion`: treadmill and motion-platform normalization.
- `ipix-haptics`: normalized tactile/force-feedback effects and safety limits.
- `ipix-vendor-*`: isolated optional adapters for documented vendor protocols.
- `ipix-sim`: virtual devices and deterministic test fixtures.

The editor/project format should store requested capabilities and fallback policy, never machine-specific device IDs or secrets.

## Rust library map

Crate names below are integration candidates, not blanket endorsements. Pin and audit exact versions during implementation. Prefer maintained standards-based crates; isolate experimental or unsafe vendor bindings behind feature flags.

| Domain | Rust crate / API | Intended role and caveat |
|---|---|---|
| OpenXR runtime | `openxr` | Primary cross-vendor XR API: sessions, views, actions, controllers, extension-based hand/eye/body tracking and haptics. Runtime and extension support vary by headset. |
| OpenXR raw bindings | `openxr-sys` (re-exported by `openxr`) | Access to extension/API surface not yet wrapped at high level. |
| SteamVR / OpenVR | `openvr` | Compatibility backend for SteamVR ecosystems and older devices; secondary to OpenXR. Requires the OpenVR runtime. |
| XR frame/render integration | `wgpu`, `ash` (Vulkan), `raw-window-handle` | Rendering interop, not device discovery. Choose renderer backend independently. |
| HID devices | `hidapi`, `hidra` | HID enumeration and reports. `hidra` is a pure-Rust candidate; validate platform coverage and maturity before selecting. |
| Raw USB | `nusb`, `rusb` | Vendor-specific USB control/bulk/interrupt transfers. Prefer OS class drivers for standard HID/audio/video devices. |
| Bluetooth LE | `btleplug` | Cross-platform BLE central/GATT access for wearables and trackers; platform and peripheral profile constraints apply. |
| Bluetooth Linux | `bluer` | Linux BlueZ integration and richer Linux-specific control. |
| Serial | `serialport`, `tokio-serial` | USB-serial bridges and documented serial protocols. |
| Linux input | `evdev`, `uinput` | Read Linux input devices and create virtual input devices; Linux-only. |
| Linux device discovery | `udev` | Hot-plug and device metadata on Linux. |
| Windows device APIs | `windows` / `windows-sys` | SetupAPI, WinRT, HID, Bluetooth and device interfaces where direct Windows integration is needed. |
| macOS device APIs | `objc2`, `io-kit` bindings / IOKit FFI | IOHIDManager and platform-specific device access; validate current crate/API maturity. |
| Network protocols | `tokio`, `socket2`, `rosc` | TCP/UDP transports and OSC devices (e.g. trackers/body tracking bridges). |
| WebSocket adapters | `tokio-tungstenite` | Documented local/network vendor APIs that expose WebSocket. |
| Camera / optical tracking | `nokhwa`, `opencv` | Camera capture and computer-vision tracking. Camera access is not equivalent to a vendor's inside-out tracking runtime. |
| AprilTag / fiducial tracking | `apriltag` bindings or OpenCV ArUco | External marker tracking; candidate integration, not a headset runtime. |
| Motion/physics mapping | `glam`, `nalgebra` | Coordinate transforms, vectors and sensor fusion math. |
| Configuration | `serde`, `toml`, `serde_json` | Device profiles and project capability requirements. |
| Async/event plumbing | `tokio`, `crossbeam-channel` | I/O tasks and bounded event delivery. Keep real-time frame path allocation-light. |

No single Rust crate currently provides universal control of all treadmills, gloves, suits, chairs or proprietary trackers. For many rows below, the correct answer is a transport crate plus a protocol adapter, not a fictional vendor-specific crate.

## Device compatibility catalogue

The catalogue aims to cover device *families* and representative products/protocols known at the time of writing. It is not a finite list of every SKU, regional revision, firmware or future product. A model is supported only when its protocol/runtime has been tested.

### Head-mounted displays, smart glasses and XR runtimes

| Family / representative products | Preferred interface | Rust integration |
|---|---|---|
| Meta Quest family (Quest, Quest 2/3/3S/Pro) | OpenXR; Android/Meta extensions and vendor tooling when needed | `openxr`; Android platform bindings via `jni` / `ndk` only for platform-specific work |
| Valve Index | SteamVR/OpenVR and available OpenXR runtime | `openxr`, fallback `openvr` |
| HTC Vive / Vive Pro / Pro 2 / XR Elite / Focus family | OpenXR where runtime exposes it; SteamVR/OpenVR for legacy paths | `openxr`, `openvr` |
| Pimax headsets | OpenXR runtime / SteamVR compatibility layer | `openxr`, `openvr` |
| Varjo XR/VR family | OpenXR plus Varjo extensions/runtime | `openxr`; vendor SDK bridge only for unsupported proprietary features |
| Windows Mixed Reality headsets | OpenXR runtime where installed; legacy WMR runtime compatibility | `openxr`; `openvr` only through SteamVR compatibility |
| Pico Neo / Pico 4 family | OpenXR / Android runtime and Pico extensions | `openxr`, Android bindings |
| Lynx R-1 | OpenXR / Android runtime where available | `openxr` |
| Bigscreen Beyond | SteamVR/OpenVR or compatible OpenXR runtime | `openxr`, `openvr` |
| PlayStation VR / PS VR2 | Platform SDK/runtime; PC adapter only where officially exposed | No generic public Rust driver; platform adapter/SDK required |
| Apple Vision Pro | visionOS spatial APIs and platform-specific app model | No direct generic Rust OpenXR backend; Swift/Objective-C host bridge, Rust core via FFI |
| XREAL Air / Beam family | USB-C DisplayPort, vendor Nebula/spatial APIs depending model | `nusb`/platform APIs for documented USB functions; vendor bridge for spatial tracking |
| VITURE XR glasses | USB-C display and vendor electrochromic/control APIs | `nusb` or HID/serial adapter only if protocol documented |
| Rokid Max / AR family | USB-C display and model-specific companion APIs | Transport crates as applicable; no universal 6DoF API |
| Epson Moverio | Model-specific Android/SDK APIs | Android bridge; `openxr` only if runtime exists |
| Magic Leap 1 / 2 | OpenXR and Magic Leap extensions/runtime | `openxr` plus vendor extension adapter |
| Microsoft HoloLens 2 | OpenXR/UWP and Microsoft extensions | `openxr` plus Windows platform adapter |
| Google Glass / enterprise smart glasses | Vendor SDK / Android APIs | Android bridge; no generic XR runtime assumption |
| Vuzix smart glasses | Vendor SDK / Android APIs | Android bridge; model-specific |
| RealWear head-worn displays | Android / vendor SDK | Android bridge; not assumed to be stereoscopic XR |

### Controllers, hand tracking, eye tracking and spatial trackers

| Device family / examples | Preferred interface | Rust integration |
|---|---|---|
| Meta Touch / Touch Plus / Touch Pro controllers | OpenXR interaction profiles | `openxr` |
| Valve Index Knuckles | OpenXR interaction profile or OpenVR | `openxr`, `openvr` |
| HTC Vive wand / Vive controllers | OpenXR / OpenVR | `openxr`, `openvr` |
| Pico controllers | OpenXR interaction profiles | `openxr` |
| Wands, gamepads and generic 6DoF controllers | HID or OpenXR runtime | `hidapi`/`hidra`, `openxr` |
| Ultraleap Leap Motion Controller / hand tracking modules | OpenXR extension if exposed, otherwise Ultraleap SDK bridge | `openxr`; vendor SDK through C ABI/FFI where required |
| Manus Prime / Quantum gloves and trackers | Manus SDK/network integration | `tokio`, `tokio-tungstenite` or UDP/OSC if supported; vendor bridge |
| Ultraleap hand tracking | OpenXR extension/runtime or vendor API | `openxr` or vendor bridge |
| Tobii eye trackers | OpenXR eye-gaze extension if runtime exposes it; Tobii SDK otherwise | `openxr`; vendor SDK bridge |
| HTC Vive Tracker family | OpenXR/SteamVR tracking runtime | `openxr`, `openvr` |
| Tundra Trackers | SteamVR tracking runtime | `openxr`, `openvr` |
| HaritoraX trackers | Vendor/SlimeVR-compatible integrations depending model | BLE via `btleplug`; OSC/UDP via `rosc`/Tokio where exposed |
| SlimeVR trackers | SlimeVR server protocol / OSC bridge | `tokio`, `rosc`, `btleplug` |
| Sony Mocopi | Vendor app/protocol bridge; OSC workflows where supported | `rosc`, `tokio`, BLE only if documented |
| Vive Ultimate Trackers | HTC runtime/vendor protocol | `openxr` where exposed; vendor bridge |
| AprilTag / ArUco marker rigs | Camera + fiducial tracking | `nokhwa` or `opencv`; AprilTag bindings |
| Lighthouse base stations | Usually consumed through SteamVR tracking stack | `openvr`; no need to reimplement radio/optical tracking in engine |

### Omnidirectional treadmills and locomotion platforms

| Product / family | Integration reality | Rust integration |
|---|---|---|
| Virtuix Omni / Omni One | Vendor software/API availability varies by model and licensing | Vendor adapter if documented; otherwise HID/USB/serial only after protocol verification using `nusb`, `hidapi`/`hidra`, `serialport` |
| KAT Walk C / C2 / C2 Core / C2 Plus / C2 Plus Family | Vendor SDK/protocol and companion software determine access | Vendor adapter; transport candidates `hidapi`, `nusb`, `btleplug`, `serialport` after device inspection |
| KAT Walk mini / mini S | Model-specific interface | Same transport candidates; no assumed common protocol |
| Infinadeck | Commercial motion platform; integration is vendor/project-specific | Vendor SDK/network adapter; `tokio`, `socket2`, `serialport` if documented |
| Cyberith Virtualizer / Virtualizer Elite | Legacy and model-specific SDK availability | Vendor adapter; `hidapi`/`nusb` only if protocol is known |
| Omni One / Omni Pro variants | Distinguish consumer and commercial hardware/software capabilities | Vendor adapter; never infer compatibility from product name |
| WalkOVR | Tracker/locomotion products vary by generation | BLE/HID/OSC adapters as exposed; `btleplug`, `hidapi`, `rosc` |
| 3DRudder | Foot-controlled motion input | HID/USB; `hidapi`/`hidra`, `nusb` |
| Natural Locomotion-compatible foot trackers | Runtime/app integration, not one universal device protocol | OpenXR/OpenVR plus tracker adapter |
| DIY omnidirectional platforms | Often Arduino/ESP32 serial, BLE or UDP | `serialport`, `tokio-serial`, `btleplug`, `tokio` |
| Motion floors / moving platforms | Proprietary industrial control and safety interlocks | Vendor API/PLC gateway; `tokio`, `socket2`, serial or fieldbus adapter after safety review |

Locomotion normalization should output planar velocity, yaw-relative direction, acceleration, confidence, calibration state and a hardware safety state. It must never directly bypass game movement constraints or physical emergency stops.

### Gloves, haptic wearables and body suits

| Product / family | Capability | Rust integration |
|---|---|---|
| HaptX Gloves (DK / G1 families) | High-fidelity tactile and force feedback | Vendor SDK/bridge required; no assumed public Rust crate |
| SenseGlove Nova / Nova 2 / DK1 | Finger tracking and force/tactile feedback depending model | Vendor SDK bridge; HID/USB only if documented; `nusb`/`hidapi` for transport |
| bHaptics TactSuit (X series / X40 / X16 / X40S) | Vibrotactile vest and ecosystem wearables | bHaptics SDK/local API bridge; `tokio`, `tokio-tungstenite` or network/serial transport only where documented |
| bHaptics TactGlove | Haptic hand feedback | Vendor SDK/API bridge |
| Manus Prime / Quantum | Finger/hand motion capture | Vendor SDK; network adapter via `tokio` if supported |
| Weart TouchDIVER | Fingertip tactile feedback | Vendor SDK bridge; no generic Rust crate assumed |
| Contact CI / Dexmo and similar exoskeleton gloves | Force feedback / hand tracking | Vendor SDK and safety adapter; transport only after protocol confirmation |
| HaptX / SenseGlove / Manus research gloves | Research and enterprise variants | Per-model vendor adapter; do not assume family-wide wire compatibility |
| Woojer vest / strap | Audio-driven haptics | Vendor app/API if available; audio-device path is not a general tactile API |
| OWO Skin / haptic suit | Electrical muscle stimulation effects | Vendor SDK only; require explicit user consent, safety limits and vendor-controlled safeguards |
| TeslaSuit | Full-body haptics, motion capture and biometrics depending configuration | Vendor SDK/enterprise integration |
| bHaptics Tactosy arms/feet/face and accessories | Localized vibrotactile feedback | bHaptics API adapter |
| Haptic vests and DIY vibration arrays | Vibration motors | HID/USB/BLE/serial/network adapter; `nusb`, `hidapi`, `btleplug`, `serialport` |
| Haptic chairs / seat pads | Vibration/transducers | HID/audio/vendor API; `cpal` for audio output, transport adapter for control |
| Haptic arm bands / wristbands | Vibration or electrical feedback | BLE GATT via `btleplug`, HID or vendor API |
| Haptic footwear / insoles | Vibration/pressure feedback | BLE GATT via `btleplug`; model-specific profile |
| Generic vibration motors / LRA / ERM controllers | Low-level haptics | USB/HID/serial/BLE transport plus a hardware-specific driver |

Safety: IPIX must treat electrical stimulation, force-feedback exoskeletons, moving platforms and high-force devices as safety-critical outputs. Require explicit opt-in, conservative limits, watchdog timeouts, emergency-stop passthrough, disconnect-to-safe-state and vendor safety interlocks. Do not synthesize electrical stimulation waveforms or bypass vendor safeguards.

### Motion capture, body tracking and biometrics

| Device family / examples | Data | Rust integration |
|---|---|---|
| Xsens MVN suits | Inertial full-body motion capture | Vendor SDK/stream adapter; `tokio`, `rosc` if OSC output |
| Perception Neuron / Noitom | IMU body tracking | Vendor protocol/Axis bridge; `tokio`, `rosc`, BLE/serial where documented |
| Rokoko Smartsuit Pro / Smartgloves | Body/hand motion capture | Rokoko Studio/streaming API adapter; `tokio`, WebSocket/UDP |
| StretchSense MoCap Pro gloves | Finger motion capture | Vendor SDK/stream adapter |
| Sony Mocopi | IMU body tracking | Vendor app/stream/OSC bridge |
| SlimeVR | IMU trackers | SlimeVR server/OSC and BLE |
| HaritoraX | IMU trackers | Vendor/compatible bridge, BLE |
| Vive Trackers / Tundra | 6DoF body/object tracking | OpenXR/OpenVR runtime |
| Polar H10 and similar heart-rate straps | Heart rate via BLE heart-rate service | `btleplug` |
| Garmin / Fitbit / Apple Watch / Samsung Galaxy Watch | Biometrics and activity; generally vendor/cloud/platform APIs, not raw game peripherals | Official APIs/platform bridge; BLE only for documented standard services |
| Generic BLE heart-rate / cadence sensors | Standard GATT profiles | `btleplug` |
| EEG headsets (Muse and research devices) | EEG/biopotential streams | Vendor SDK or LSL/network bridge; `tokio` and OSC/UDP adapters |
| OpenBCI boards | Biosignal acquisition | Serial/USB via `serialport`/`nusb`; protocol-specific decoder |
| Eye trackers (Tobii and research models) | Gaze vectors and pupil data | OpenXR extension or vendor SDK bridge |

Biometric data is sensitive. The runtime must keep it opt-in, minimize retention, expose permission state to the player, and avoid uploading it by default.

### Other physical controls and simulation hardware

| Device family | Rust integration |
|---|---|
| Gamepads (Xbox, PlayStation, Nintendo, generic) | `gilrs` for common gamepad input; platform APIs/HID fallback |
| Joysticks, HOTAS, flight sticks | `gilrs` where supported; HID via `hidapi`/`hidra` |
| Steering wheels (Logitech, Thrustmaster, Fanatec, Moza, Simagic) | HID/evdev/Windows APIs; force feedback is vendor/protocol-specific |
| Pedals, shifters, handbrakes | HID/USB; `hidapi`/`hidra`, `nusb` |
| Racing seats / motion rigs (DOF Reality, Next Level Racing, D-BOX, etc.) | Vendor SDK, SimHub/telemetry bridge, serial/network adapter |
| Flight/racing cockpit switches and button boxes | HID; `hidapi`/`hidra` |
| MIDI controllers / foot controllers | `midir` |
| OSC controllers / sensor boards | `rosc` + `tokio` |
| MIDI/DMX stage devices | `midir`; DMX-over-USB/network adapter |
| 3Dconnexion SpaceMouse | HID/vendor protocol; `hidapi`/`hidra` |
| Accessibility switches, adaptive controllers and sip-and-puff interfaces | OS accessibility/input APIs, HID, serial; preserve OS accessibility semantics |
| Custom Arduino / Raspberry Pi Pico / ESP32 controllers | USB HID, serial, BLE GATT or UDP; `nusb`, `serialport`, `btleplug`, `tokio` |
| Industrial motion controllers / PLCs | Vendor/fieldbus gateway only; separate safety-rated controller from game process |

## Capability vocabulary

Initial capability IDs (versioned before becoming a stable public format):

- `xr.head_pose.6dof`, `xr.stereo_views`, `xr.passthrough`, `xr.spatial_anchors`
- `input.controller.pose`, `input.controller.buttons`, `input.controller.axes`
- `tracking.hand.skeleton`, `tracking.finger.joints`, `tracking.eye.gaze`, `tracking.body.skeleton`, `tracking.object.pose`
- `locomotion.planar_velocity`, `locomotion.yaw`, `locomotion.acceleration`, `locomotion.safety_state`
- `haptics.vibration`, `haptics.tactile`, `haptics.force_feedback`, `haptics.localized`
- `biometrics.heart_rate`, `biometrics.respiratory_rate`, `biometrics.eeg` (opt-in and privacy-gated)
- `input.accessibility.switch`, `input.accessibility.adaptive`

Capabilities need metadata: units, coordinate frame, handedness, confidence, sample timestamp, update rate, permission/consent, calibration and safety state.

## Device identity and matching

A registry record should include:

- Stable internal UUID (never use serial number as a public player identifier).
- Transport identity: USB VID/PID/interface, HID usage/page, BLE service UUIDs, runtime path or network endpoint.
- Manufacturer/model/firmware strings when available.
- Driver and protocol version.
- Capabilities discovered, capabilities inferred, and confidence for each.
- Permission, consent and safety status.
- Calibration profile reference (stored locally and user-controlled).

Matching priority:

1. Standard runtime/protocol identity (OpenXR interaction profile, standard GATT service).
2. Exact vendor + product + interface + known firmware range.
3. Explicit user-selected profile.
4. Generic class profile with reduced capability claims.
5. Unknown device: expose metadata only; never send speculative output reports.

Never auto-install or execute downloaded drivers. Third-party adapters must be signed, versioned, permission-scoped and sandboxed where the OS permits.

## Runtime and safety requirements

- Hot-plug and disconnect handling without crashing or blocking the render thread.
- Bounded queues, timestamps, stale-sample detection and per-device health.
- Explicit coordinate-system conversion and calibration.
- No untrusted network listener by default; bind local bridges to loopback unless configured.
- Authentication/pairing for network and BLE devices where supported.
- Emergency stop must bypass game logic and remain under hardware/vendor control.
- Output watchdogs; disconnect, crash or timeout returns actuators to safe/off state.
- Per-category permissions, especially eye tracking, biometrics, cameras and body tracking.
- No biometric collection or remote transmission by default.
- Deterministic virtual devices for tests and CI.
- Graceful fallback when optional capabilities are absent.

## Implementation phases

1. **Foundation:** `ipix-core` capability types, device registry schema, simulated devices and documentation.
2. **Standards:** OpenXR headset/controllers/haptics backend; desktop HID/gamepad discovery.
3. **Transport:** USB, BLE, serial and OSC backends with permission and safety boundaries.
4. **Locomotion:** normalized treadmill API and adapters only for devices with documented/tested protocols.
5. **Wearables:** hand/body tracking and haptic output adapters, starting with public standards and vendor-supported SDKs.
6. **Certification matrix:** OS/runtime/device/firmware test matrix; compatibility claims require reproducible tests.

## Validation policy

A catalogue entry is not a compatibility claim. Track each adapter as one of:

- **Standard backend:** implemented against a public standard and tested on named hardware/runtime.
- **Vendor adapter:** implemented against a vendor-supported SDK/API and tested on named model/firmware.
- **Transport candidate:** transport is available, but protocol is not yet implemented or verified.
- **Research only:** public information is insufficient for a reliable implementation.
- **Unsupported/proprietary:** no documented integration path currently known.

Review sources and protocol availability before promoting a product from candidate to supported. Re-check vendor SDK terms, redistribution restrictions and platform policies before shipping.

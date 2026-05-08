# Mobile Camera Frame Upload

Issue: #33 Upload one mobile JPEG frame to PiFinder.

Status: implemented as storage-only debug plumbing.

## Goal

Move one JPEG captured by Android Camera Lab to PiFinder so we can collect real
mobile-camera evidence on the Raspberry without coupling mobile images to the
solver or integrator yet.

This is intentionally not a live plate-solving feature.

## Android Flow

1. Open Camera Lab.
2. Run a JPEG capture mode, preferably `Solve Candidate Burst`.
3. Camera Lab remembers the latest captured JPEG in memory.
4. Press `Upload Last JPEG`.
5. Android sends a multipart request to:

```text
<PiFinder base URL>/mobile/camera_frame
```

The PiFinder base URL is the same setting used by PiFinder Remote and the
mobile bridge test actions.

## Request Shape

```http
POST /mobile/camera_frame
Content-Type: multipart/form-data
```

Required parts:

```text
metadata: JSON object encoded as UTF-8 text
frame: JPEG binary file part
```

The Android metadata includes:

- schema name;
- device manufacturer/model/API level;
- camera ID and camera selection label;
- capture mode;
- source filename;
- JPEG orientation;
- active capture size when available;
- storage/solver flags.

## PiFinder Storage

PiFinder stores the upload under:

```text
~/PiFinder_data/mobile/frames/
```

Each upload creates:

```text
<frame_id>.jpg
<frame_id>.json
```

The JSON sidecar records:

- received UTC timestamp;
- generated frame ID;
- original filename;
- content type;
- byte count;
- stored paths;
- raw Android metadata;
- `storage_only: true`;
- `solver_invoked: false`.

## Validation Rules

The endpoint rejects the request with `400` when:

- the `frame` file part is missing or empty;
- the `metadata` part is missing;
- `metadata` is not valid JSON;
- `metadata` is not a JSON object;
- the frame does not start with JPEG magic bytes;
- the frame is larger than 25 MiB.

## Guardrails

This feature must not:

- invoke PiFinder's solver;
- update live pointing state;
- feed the integrator;
- change classic PiFinder camera behavior;
- assume the mobile camera is reliable enough for solving.

The next safe steps are image quality scoring and explicit diagnostic solving
for stored files.

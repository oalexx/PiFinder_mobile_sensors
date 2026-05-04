# Mobile Remote Layout

Issue: [#16 Improve PiFinder web remote mobile layout](https://github.com/oalexx/PiFinder_mobile_sensors/issues/16)

## Goal

Make the existing `/remote` page easier to use from a phone without changing the
PiFinder backend or the key callback protocol.

## Changes

Files changed:

- `python/views/header.tpl`
- `python/views/remote.tpl`
- `python/views/css/style.css`
- `PiFinder_lite/upstream_change_log.md`

The layout update:

- replaces inline layout styles with reusable CSS classes;
- keeps the same button codes sent to `/key_callback`;
- keeps `Ent+` and `Long` as next-key modifiers;
- increases button height for more reliable touch input;
- keeps a stable four-column keypad;
- constrains the PiFinder screen image for small phone widths;
- uses HTML entities for arrows and square symbol to avoid encoding problems.
- adds a version query to `style.css` so mobile browsers do not reuse the old
  cached remote styles.

## Behavior Preserved

The following behavior is intentionally unchanged:

- `/remote` still renders through the existing Bottle template.
- `/image` is still polled by the page.
- `/key_callback` still receives `{ "button": code }`.
- Existing button codes such as `A`, `B`, `C`, `D`, `UP`, `DN`, `SQUARE`,
  `ALT_*`, and `LNG_*` are unchanged.

## Validation

Run the local endpoint validator:

```bash
cd python/
.\.conda-py39\python.exe ..\PiFinder_lite\validate_remote_endpoints.py --port 18080
```

For visual phone validation from the development PC:

```bash
cd python/
.\.conda-py39\python.exe ..\PiFinder_lite\validate_remote_endpoints.py --serve --host 0.0.0.0 --port 18080
```

Then open from the phone:

```text
http://<pc-lan-ip>:18080/remote
```

Checks:

1. Remote page loads without horizontal scrolling.
2. Screen image is readable and centered.
3. Buttons are comfortable to tap.
4. `Ent+` and `Long` modifiers still toggle correctly.
5. Direction, number, plus/minus, and square buttons still submit without error.

Local phone validation from the development PC:

- URL used: `http://192.168.8.167:18080/remote`
- Browser: Brave on Android.
- Result: the updated CSS loaded after adding the `style.css` version query.
- The remote now renders as a stable four-column grid.
- The screen image is centered and readable.
- Touch targets are substantially larger and easier to press.
- Arrow and square symbols render correctly.
- The final row has three controls and an empty fourth grid slot because the
  remote currently has 19 controls. This is acceptable for the first mobile
  layout pass.

## Raspberry Validation

Repeat the same visual checks on Raspberry Pi using:

```bash
cd python/
python3.9 -m PiFinder.main -fh --camera debug --keyboard none -x
```

Open:

```text
http://<pifinder-ip>/remote
```

or:

```text
http://<pifinder-ip>:8080/remote
```

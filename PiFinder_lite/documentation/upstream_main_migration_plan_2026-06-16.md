# Upstream `main` Migration Plan

> **For agentic workers:** This is a fork-migration plan, not a greenfield feature.
> Execute it on a dedicated branch/worktree, task-by-task, committing after each task.
> The existing mobile test suite (`python/tests/test_mobile_*.py`) is the regression
> gate — port a piece, run the relevant test, keep it green.

**Goal:** Bring the mobile/Lite fork from its current base (`upstream/release @ 651e23fe`)
onto `upstream/main` (88 commits ahead), absorbing the Bottle→Flask webserver rewrite,
the official headless `/remote` mode, and the integrator/solver advances, while keeping
all mobile-bridge, Lite, and Android capabilities working and additive.

**Architecture:** The fork's heavy logic lives in standalone modules
(`mobile_bridge.py`, `PiFinder_lite/*`) that upstream does not touch. `server.py` only
holds thin `@app.route` shims that delegate to `mobile_bridge`. So the migration is
dominated by **re-registering ~12 routes in Flask style** and reconciling a handful of
small core-file patches — not by rewriting business logic.

**Tech Stack:** Python 3.9/3.13, Flask 3.0.3 (was Bottle 0.12), flask-babel, waitress,
Android/Gradle, pytest. tetra3 (vendored), numpy 1.26.4, pandas 2.0.3, pyerfa.

---

## 0. Current State (measured 2026-06-16)

| Fact | Value |
|------|-------|
| Common ancestor (last resync point) | `651e23fe` (upstream "Adjust dovetail bottom") |
| `upstream/release` ahead of ancestor | **7 commits** (docs + case files only — zero overlap with fork) |
| `upstream/main` ahead of ancestor | **88 commits, 316 files** |
| Fork commits on top of ancestor | **4** (`be267802`, `92f8319a`, `a306de67`, `84b2b48b`) |
| Uncommitted WIP in working tree | **322 lines** across `mobile_bridge.py`, `server.py`, `MainActivity.java`, 3 tests |
| Files both fork **and** `main` touch (conflict surface) | 8: `server.py`, `solver.py`, `utils.py`, `ui/marking_menus.py`, `ui/preview.py`, `keyboard_none.py`, `README.md`, `CLAUDE.md` |

### What `main` brings (the reason to migrate)

| Commit | Feature | Impact on fork |
|--------|---------|----------------|
| `9e96d222` #331 | **Webserver migrated Bottle → Flask + Jinja** | **Largest cost.** All `python/views/*` rewritten; `server.py` +906/−663. Fork's 12 routes must be re-registered in Flask. |
| `feccb8b4` #435 | **Headless remote-control mode + `pifinder-remote` skill** | Official `/remote` now exists upstream → collides with fork's Lite `/remote`. Decision needed. |
| `e17f621f` #459 | Polar alignment (eq platforms/mounts) | Additive; verify it coexists with mobile IMU overlay guardrails. |
| `7b148bbe` #423 | FastAltAz rewrite via pyerfa | New deps `pyerfa`, `numpy-quaternion`. |
| `dc39e11b` #388 | IMU Integrator Selection | Touches integrator — keep mobile IMU out of it (guardrail). |
| `f0195490` #338 | Eq-mount IMU dead-reckoning | Same guardrail. |
| `cce9c02b` #336 | Contrast reserve | `ui/preview.py` rewrite (fork has a 3-line patch there). |

### Dependency delta `651e23fe → upstream/main`
```
- bottle==0.12.25            (REMOVED)
+ Flask==3.0.3               (NEW)
+ flask-babel==4.0.0         (NEW)
+ waitress==3.0.1            (NEW)
+ pyerfa==2.0.1.5            (NEW)
+ numpy-quaternion==2023.0.4 (NEW)
  numpy   1.26.2 -> 1.26.4   (minor — fork's NumPy/tetra3 shim stays valid)
  pandas  1.5.3  -> 2.0.3    (MAJOR — watch catalog import code)
  pydeepskylog 1.3.2 -> 1.6
```

---

## DECISIONS TO LOCK BEFORE EXECUTING

These are not mechanical; resolve them first (they change the tasks):

- **D1 — `/remote` ownership.** Upstream now ships an official `/remote`. Options:
  (a) adopt upstream's `/remote` and drop the fork's Lite remote;
  (b) keep the fork's remote but move it to a namespaced path (e.g. `/mobile/remote` or `/lite`);
  (c) merge both into the official `/remote`.
  **Recommended:** (b) namespace the fork remote to `/mobile/remote` short-term, evaluate
  adopting upstream's in a follow-up. Keeps both working, zero behavior loss.
- **D2 — `keyboard_none.py`.** File existed pre-split; both sides made 4–8 line tweaks.
  **Recommended:** take upstream's version as the base, re-apply the fork's tweak only if
  it adds something upstream's lacks (likely it doesn't — verify in Task 5).
- **D3 — Rebase vs merge.** Fork history is linear (4 commits replanted on upstream).
  **Recommended:** `git rebase --onto upstream/main 651e23fe` to preserve the linear,
  additive style. A merge commit is the fallback if conflict volume is unmanageable.
- **D4 — tetra3 shims.** Fork commits `a306de67` (NumPy compat) and `92f8319a` (protobuf
  import path) were workarounds. numpy stays 1.26.x so they likely remain valid; `main`
  committed a tetra3 symlink (`0a8262fa`). Verify in Task 7 whether they're still needed.

---

## Phase 1 — Pre-flight (no history rewrite yet)

### Task 1: Preserve the 322 lines of WIP
**Files:** `mobile_bridge.py`, `server.py`, `MainActivity.java`, `test_mobile_*.py` (working tree)

- [ ] **Step 1: Confirm what the WIP is**
  Run: `git diff --stat`
  Expected: 6 files, ~322 insertions.
- [ ] **Step 2: Commit it onto the current branch so the rebase has a clean tree**
  ```bash
  git add python/PiFinder/mobile_bridge.py python/PiFinder/server.py \
          mobile/app/src/main/java/io/pifinder/mobile/MainActivity.java \
          python/tests/test_mobile_bridge.py \
          python/tests/test_mobile_android_calibration_ui.py \
          python/tests/test_mobile_android_camera_solve_ui.py
  git commit -m "wip: mobile bridge changes before upstream/main migration"
  ```
  Expected: clean tree (`git status -sb` shows no `M`).

### Task 2: Create an isolated migration branch + safety tag
- [ ] **Step 1: Tag the current tip as a rollback point**
  ```bash
  git tag pre-main-migration-2026-06-16
  ```
- [ ] **Step 2: Branch for the migration**
  ```bash
  git switch -c codex/upstream-main-migration-20260616
  ```
- [ ] **Step 3: Verify fetch is current**
  Run: `git fetch upstream --tags && git log --oneline -1 upstream/main`
  Expected: tip is `19717fb2` (or newer).

### Task 3: Snapshot the current green test baseline (regression reference)
- [ ] **Step 1: Run the mobile/Lite suite on the OLD base and record pass count**
  ```bash
  ./python/.venv/Scripts/python.exe -m pytest \
    python/tests/test_mobile_bridge.py python/tests/test_mobile_camera_profile.py \
    python/tests/test_mobile_imu_analysis.py python/tests/test_lite_runtime_compat.py \
    python/tests/test_mobile_mount_offset.py python/tests/test_mobile_mount_repeatability.py \
    python/tests/test_mobile_android_calibration_ui.py \
    python/tests/test_mobile_android_camera_solve_ui.py -q
  ```
  Expected: all pass. **Write the number down** — this is the target after migration.

---

## Phase 2 — Replant onto `upstream/main`

### Task 4: Rebase the 4 fork commits + WIP onto `upstream/main` (D3)
**Files:** all (history operation)

- [ ] **Step 1: Start the rebase**
  ```bash
  git rebase --onto upstream/main 651e23fe codex/upstream-main-migration-20260616
  ```
- [ ] **Step 2: Resolve conflicts by category as they appear**
  - **Additive-only files** (`PiFinder_lite/*`, `mobile/*` except none, new tests,
    `mobile_bridge.py`, `keyboard_none.py` new content): take fork side (`git checkout --theirs`
    is *not* reliable in rebase; resolve by keeping the fork's additions). These should mostly
    apply cleanly since upstream never created them.
  - **`server.py`**: **expect a hard conflict** — upstream replaced the whole Bottle server
    with Flask. **Do NOT hand-merge line by line.** Take **upstream's Flask `server.py` wholesale**
    (`git checkout upstream/main -- python/PiFinder/server.py`), then `git add` it. The fork's
    route shims get re-added in Phase 3, not merged here.
  - **`solver.py`, `utils.py`, `ui/preview.py`, `ui/marking_menus.py`**: take **upstream's**
    version, note the fork's small patch (4 / 37 / 3 / 6 lines) for re-application in Task 8.
  - **`keyboard_none.py`**: take **upstream's** (D2).
  - **`README.md`, `CLAUDE.md`**: take **fork's** (they document fork state).
- [ ] **Step 3: Capture the fork's old route shims before they're lost**
  Before continuing, save the fork's Bottle routes for reference:
  ```bash
  git show pre-main-migration-2026-06-16:python/PiFinder/server.py > /tmp/fork_old_server.py
  ```
- [ ] **Step 4: Finish the rebase**
  ```bash
  git rebase --continue   # repeat until done
  ```
  Expected: branch now sits on top of `19717fb2` with fork additions present and
  `server.py` == upstream Flask version (mobile routes temporarily absent).

---

## Phase 3 — Re-register the 12 mobile routes in Flask

The handlers are thin and delegate to `mobile_bridge.py`. Port the **route registration**,
not the logic. Reference: `/tmp/fork_old_server.py` (the Bottle versions).

### Bottle → Flask translation rules
| Bottle | Flask 3.0.3 |
|--------|-------------|
| `@app.route("/x", method="POST")` | `@app.route("/x", methods=["POST"])` |
| `request.json` | `request.get_json(silent=True)` |
| `request.forms.get("k")` | `request.form.get("k")` |
| `return some_dict` | `return jsonify(some_dict)` (explicit; Flask 3 auto-jsons dicts but be explicit) |
| `request.files.get("f")` | `request.files.get("f")` (same API) |
| `<id:int>` | `<int:id>` |
| `response.content_type = "..."` | `return Response(body, mimetype="...")` |

### Task 5: Port the read-only GET routes first (lowest risk)
**Files:** Modify `python/PiFinder/server.py` (inside `Server.__init__`, near upstream's `/remote`)
**Test:** `python/tests/test_mobile_bridge.py`

Routes: `/mobile/status`, `/mobile/mount_profile`, `/mobile/optical_boresight`,
`/mobile/camera_reports`.

- [ ] **Step 1:** Add the four GET routes using the Flask form. Example for `/mobile/status`
  (adapt the others identically — they already return dicts from `mobile_bridge`):
  ```python
  @app.route("/mobile/status")
  def mobile_status():
      payload = mobile_bridge.status_payload()
      mobile_bridge.write_debug_json("status.json", payload)
      return jsonify(payload)
  ```
- [ ] **Step 2:** Ensure `from PiFinder import ... mobile_bridge` import is present at top of
  `server.py` (upstream's import block, line ~14). Add `mobile_bridge` to it.
- [ ] **Step 3: Run** `pytest python/tests/test_mobile_bridge.py -q`
  Expected: GET-route tests pass.
- [ ] **Step 4: Commit** `git commit -am "feat(mobile): port read-only routes to Flask"`

### Task 6: Port the POST routes
**Files:** `python/PiFinder/server.py`  **Test:** `test_mobile_bridge.py`,
`test_mobile_camera_profile.py`

Routes: `/mobile/profile`, `/mobile/environment`, `/mobile/gps`, `/mobile/imu`,
`/mobile/imu_drift_analysis`, `/mobile/camera_frame`, `/mobile/camera_solve`.

- [ ] **Step 1:** Port each POST route. Convert `method="POST"`→`methods=["POST"]` and
  `request.json`→`request.get_json(silent=True)`; `/mobile/camera_frame` uses
  `request.files.get(...)` (unchanged). Wrap dict returns in `jsonify`.
- [ ] **Step 2: Run** the two tests above `-q`. Expected: pass.
- [ ] **Step 3:** Decide and apply **D1** for `/remote` (recommended: register the fork
  remote at `/mobile/remote`, leave upstream's `/remote` untouched).
- [ ] **Step 4: Commit** `git commit -am "feat(mobile): port POST routes + namespace lite remote to Flask"`

---

## Phase 4 — Re-apply core patches & reconcile

### Task 7: Verify tetra3 shims (D4)
**Files:** wherever `a306de67` and `92f8319a` applied (numpy compat + protobuf import path)
- [ ] **Step 1:** Inspect what those commits changed:
  `git show 92f8319a --stat && git show a306de67 --stat`
- [ ] **Step 2:** Check whether `upstream/main`'s tetra3 handling already covers it
  (it committed a symlink `0a8262fa`). Try importing without the shim:
  `./python/.venv/Scripts/python.exe -c "import PiFinder.solver"`
- [ ] **Step 3:** If import works clean, drop the shim; if it errors, re-apply the shim and
  note it in `PiFinder_lite/documentation/upstream_change_log.md`.

### Task 8: Re-apply the small core-file patches
**Files:** `solver.py` (+4), `utils.py` (+37), `ui/preview.py` (+3), `ui/marking_menus.py` (+6)
- [ ] **Step 1:** For each, diff the fork's old patch and re-apply by hand onto upstream's
  rewritten version:
  `git show pre-main-migration-2026-06-16:python/PiFinder/utils.py | diff - <(git show 651e23fe:python/PiFinder/utils.py)`
  (repeat per file) and port the intent.
- [ ] **Step 2:** Confirm the fork's reason for each patch still exists in main; if upstream
  already added equivalent behavior, skip it.
- [ ] **Step 3: Commit** `git commit -am "fixup: re-apply mobile core patches onto main"`

---

## Phase 5 — Dependencies & environment

### Task 9: Rebuild the Python env on the new requirements
- [ ] **Step 1:** Merge the fork's extra deps (if any in `requirements-trixie-py313.txt`)
  with upstream's new `requirements.txt` (Flask/waitress/flask-babel/pyerfa/numpy-quaternion).
- [ ] **Step 2:** `pip install -r python/requirements.txt -r python/requirements_dev.txt`
- [ ] **Step 3:** Smoke import: `python -c "import flask, waitress, flask_babel, erfa, quaternion"`
  Expected: no ImportError.
- [ ] **Step 4:** Watch the **pandas 1.5→2.0** bump — run catalog-touching tests:
  `pytest -m smoke -q`. Fix any pandas-2 deprecations surfaced.

---

## Phase 6 — Validation gates

### Task 10: Full regression vs the Task 3 baseline
- [ ] **Step 1:** Re-run the exact Task 3 command. Expected: **same pass count or higher**.
- [ ] **Step 2:** Run the broader suites: `pytest -m smoke -q` and `pytest -m unit -q`.
- [ ] **Step 3:** Launch headless and hit the ported routes manually:
  ```bash
  python -m PiFinder.main -fh --camera debug --keyboard none -x
  # then: curl http://localhost:<port>/mobile/status   -> JSON
  #       curl http://localhost:<port>/remote           -> upstream remote UI
  #       curl http://localhost:<port>/mobile/remote     -> fork lite remote (if D1=b)
  ```
- [ ] **Step 4:** Build the Android app unchanged: `cd mobile && ./gradlew.bat assembleDebug`.
  Verify it still talks to the Pi (endpoints unchanged from the app's perspective).

### Task 11: Update fork documentation & guardrails
- [ ] **Step 1:** Append this migration to `PiFinder_lite/documentation/upstream_change_log.md`.
- [ ] **Step 2:** Update `CLAUDE.md` "Current Project Context" to note the Flask base and the
  `/remote` decision (D1).
- [ ] **Step 3:** Re-confirm the guardrails still hold against `main`'s new integrator code:
  mobile IMU and mobile camera solves must **not** feed the (now eq-mount-aware) integrator.
- [ ] **Step 4: Commit** and open a PR from `codex/upstream-main-migration-20260616`.

---

## Rollback

If the migration becomes unmanageable at any point:
```bash
git rebase --abort                       # mid-rebase
git switch codex/upstream-release-resync-20260515
git tag -d pre-main-migration-2026-06-16 # optional
```
The `pre-main-migration-2026-06-16` tag preserves the exact pre-migration tip.

## Risk Register
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Flask `server.py` port misses an endpoint behavior | Med | Existing `test_mobile_bridge.py` covers each route; port = green test |
| `/remote` collision breaks one of the two UIs | Med | D1 namespacing keeps both; decide before Task 6 |
| pandas 2.0 breaks catalog import | Low-Med | Task 9 Step 4 runs smoke tests; isolated from mobile code |
| Integrator changes tempt mobile IMU coupling | Low | Guardrail re-check in Task 11 Step 3 |
| tetra3 shim conflicts with main's symlink | Low | Task 7 verifies import before keeping/dropping shim |

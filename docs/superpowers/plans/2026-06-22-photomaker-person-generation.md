# PhotoMaker Person-Image Generation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Photo of a person → new photos" mode that takes 1–4 reference photos plus a prompt and returns new images of that person via Runware PhotoMaker.

**Architecture:** New `generate_person_images()` in `runware.py` calls Runware with `taskType: "photoMaker"`. New `POST /api/generate-person` endpoint mirrors the existing `/api/generate` (auth, credits, history) but accepts base64 reference images. Frontend `index.html` gains a mode toggle and a photo-upload UI; the existing text-to-image mode is untouched.

**Tech Stack:** FastAPI, SQLAlchemy, httpx (backend); vanilla HTML/CSS/JS (frontend); pytest.

Spec: `docs/superpowers/specs/2026-06-22-photomaker-person-generation-design.md`

---

## File Structure

- Modify: `image-gen-api/runware.py` — add `_ensure_img_trigger()` helper and `generate_person_images()`.
- Modify: `image-gen-api/main.py` — add `GeneratePersonRequest` model and `POST /api/generate-person`.
- Create: `image-gen-api/tests/test_generate_person.py` — endpoint + helper tests.
- Modify: `image-gen/index.html` — mode toggle + photo upload UI + JS call.

---

## Task 1: Trigger-word helper + PhotoMaker Runware call

**Files:**
- Modify: `image-gen-api/runware.py`
- Test: `image-gen-api/tests/test_generate_person.py`

PhotoMaker requires the token `img` somewhere in the prompt. `_ensure_img_trigger`
guarantees it without duplicating. `generate_person_images` builds the
`photoMaker` payload. The Runware HTTP call itself is not unit-tested (the
existing `generate_images` isn't either); it is exercised via the endpoint with
the function mocked in Task 2. Only the pure helper is unit-tested here.

- [ ] **Step 1: Write the failing test for the helper**

Create `image-gen-api/tests/test_generate_person.py`:

```python
from runware import _ensure_img_trigger


def test_trigger_added_when_missing():
    assert _ensure_img_trigger("a man in a suit") == "a man in a suit img"


def test_trigger_not_duplicated_when_present():
    assert _ensure_img_trigger("a man img in a suit") == "a man img in a suit"


def test_trigger_word_boundary_not_fooled_by_substring():
    # "image" contains "img"? no, but "imgur" would; ensure whole-word check
    assert _ensure_img_trigger("imgur logo") == "imgur logo img"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd image-gen-api && python -m pytest tests/test_generate_person.py -v`
Expected: FAIL with `ImportError: cannot import name '_ensure_img_trigger'`

- [ ] **Step 3: Implement helper + PhotoMaker call**

In `image-gen-api/runware.py`, add after the existing imports/constants:

```python
import re

PHOTOMAKER_MODEL = "civitai:139562@344487"  # RealVisXL V4.0 (SDXL). Verify availability in Step 5.


def _ensure_img_trigger(prompt: str) -> str:
    if re.search(r"\bimg\b", prompt):
        return prompt
    return f"{prompt} img"


async def generate_person_images(
    prompt: str,
    input_images: list[str],
    width: int,
    height: int,
    count: int,
    style: str = "Photographic",
    strength: int = 20,
) -> list[str]:
    api_key = os.getenv("RUNWARE_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWARE_API_KEY not set")

    payload = [
        {
            "taskType": "photoMaker",
            "taskUUID": str(uuid.uuid4()),
            "model": PHOTOMAKER_MODEL,
            "inputImages": input_images,
            "style": style,
            "strength": strength,
            "positivePrompt": _ensure_img_trigger(prompt),
            "width": width,
            "height": height,
            "numberResults": count,
            "steps": 30,
            "CFGScale": 7.0,
            "outputFormat": "WEBP",
        }
    ]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            RUNWARE_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["imageURL"] for item in data["data"]]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd image-gen-api && python -m pytest tests/test_generate_person.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Verify PhotoMaker model AIR id is valid**

The `PHOTOMAKER_MODEL` must be an SDXL model available on Runware. Confirm
`civitai:139562@344487` resolves in the Runware model catalog
(https://runware.ai/docs/image-inference/photomaker). If it does not, pick any
available SDXL checkpoint AIR id from the catalog and update the constant. This
is a config value only — no test change needed.

- [ ] **Step 6: Commit**

```bash
git add image-gen-api/runware.py image-gen-api/tests/test_generate_person.py
git commit -m "feat(image-gen): add PhotoMaker generate_person_images + img-trigger helper"
```

---

## Task 2: `/api/generate-person` endpoint

**Files:**
- Modify: `image-gen-api/main.py`
- Test: `image-gen-api/tests/test_generate_person.py`

Mirrors `/api/generate`: same auth, same credit rules, saves to `Generation`
with `settings={"mode": "person"}`. Validates 1–4 input images.

- [ ] **Step 1: Write the failing endpoint tests**

Append to `image-gen-api/tests/test_generate_person.py`:

```python
from unittest.mock import patch, AsyncMock

MOCK_URLS = ["https://cdn.runware.ai/person1.webp"]
IMG = "data:image/png;base64,AAAA"


def _token(client, username, password):
    return client.post("/api/login", json={"username": username, "password": password}).json()["token"]


def test_generate_person_success(client):
    token = _token(client, "client1", "pass123")
    with patch("main.generate_person_images", new_callable=AsyncMock, return_value=MOCK_URLS):
        resp = client.post("/api/generate-person",
            json={"prompt": "in a suit", "input_images": [IMG], "count": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["image_urls"] == MOCK_URLS
    assert resp.json()["credits"] == 9


def test_generate_person_requires_at_least_one_image(client):
    token = _token(client, "client1", "pass123")
    resp = client.post("/api/generate-person",
        json={"prompt": "in a suit", "input_images": [], "count": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_generate_person_rejects_more_than_four_images(client):
    token = _token(client, "client1", "pass123")
    resp = client.post("/api/generate-person",
        json={"prompt": "in a suit", "input_images": [IMG] * 5, "count": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_generate_person_no_credits(client):
    from models import User
    from tests.conftest import TestingSession
    db = TestingSession()
    db.query(User).filter(User.username == "client1").update({"credits": 0})
    db.commit()
    db.close()

    token = _token(client, "client1", "pass123")
    resp = client.post("/api/generate-person",
        json={"prompt": "in a suit", "input_images": [IMG], "count": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 402


def test_generate_person_admin_bypasses_credits(client):
    token = _token(client, "admin", "admin123")
    with patch("main.generate_person_images", new_callable=AsyncMock, return_value=MOCK_URLS):
        resp = client.post("/api/generate-person",
            json={"prompt": "in a suit", "input_images": [IMG], "count": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200


def test_generate_person_no_auth(client):
    resp = client.post("/api/generate-person",
        json={"prompt": "in a suit", "input_images": [IMG]})
    assert resp.status_code in (401, 422)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd image-gen-api && python -m pytest tests/test_generate_person.py -v`
Expected: endpoint tests FAIL with 404 (route not found) / errors.

- [ ] **Step 3: Implement the endpoint**

In `image-gen-api/main.py`, update the import on line 11 from:

```python
from runware import generate_images, CREDITS_PER_IMAGE
```
to:
```python
from runware import generate_images, generate_person_images, CREDITS_PER_IMAGE
```

Then add after the existing `/api/generate` route (after the `return` of
`generate`, before `/api/history`):

```python
class GeneratePersonRequest(BaseModel):
    prompt: str
    input_images: list[str]
    width: int = 1024
    height: int = 1024
    count: int = 1


@app.post("/api/generate-person")
async def generate_person(req: GeneratePersonRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not (1 <= len(req.input_images) <= 4):
        raise HTTPException(status_code=422, detail="Provide between 1 and 4 reference images")

    if not user.is_admin:
        cost = req.count * CREDITS_PER_IMAGE
        if user.credits < cost:
            raise HTTPException(status_code=402, detail="Insufficient credits")

    image_urls = await generate_person_images(
        prompt=req.prompt,
        input_images=req.input_images,
        width=req.width,
        height=req.height,
        count=req.count,
    )

    if not user.is_admin:
        user.credits -= req.count * CREDITS_PER_IMAGE

    gen = Generation(
        user_id=user.id,
        prompt=req.prompt,
        negative_prompt="",
        settings={"width": req.width, "height": req.height, "mode": "person"},
        image_urls=image_urls,
    )
    db.add(gen)
    db.commit()
    db.refresh(gen)

    return {"id": gen.id, "image_urls": image_urls, "credits": user.credits}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd image-gen-api && python -m pytest tests/test_generate_person.py -v`
Expected: PASS (all tests, helper + endpoint)

- [ ] **Step 5: Run the full suite to confirm no regressions**

Run: `cd image-gen-api && python -m pytest -v`
Expected: all existing tests still PASS.

- [ ] **Step 6: Commit**

```bash
git add image-gen-api/main.py image-gen-api/tests/test_generate_person.py
git commit -m "feat(image-gen): add /api/generate-person endpoint"
```

---

## Task 3: Frontend mode toggle + photo upload

**Files:**
- Modify: `image-gen/index.html`

Add a two-button mode toggle. Default mode = existing text-to-image (unchanged
behaviour). Person mode shows a file input (up to 4), thumbnails, the prompt
field, and calls `/api/generate-person` with base64 data URIs. Result rendering
and credit display reuse the existing logic. No automated tests (static page);
verified manually.

- [ ] **Step 1: Read current structure**

Read `image-gen/index.html` fully to locate: the generate button/handler, the
prompt input id, the result-rendering function, and the `credits` display
update. Reuse these — do not duplicate rendering logic.

- [ ] **Step 2: Add the mode toggle UI**

Above the prompt field, add:

```html
<div class="mode-toggle">
  <button type="button" id="mode-text" class="mode-btn active">Текст → фото</button>
  <button type="button" id="mode-person" class="mode-btn">Фото человека → новые фото</button>
</div>

<div id="person-controls" style="display:none;">
  <label class="upload-label">
    Загрузи 1–4 фото человека:
    <input type="file" id="person-files" accept="image/*" multiple>
  </label>
  <div id="person-thumbs" class="thumbs"></div>
</div>
```

Match the file's existing CSS style (reuse existing classes/colors; add minimal
`.mode-toggle`, `.mode-btn`, `.thumbs` rules consistent with the current look).

- [ ] **Step 3: Add mode-switch + file-handling JS**

In the page `<script>`, add (using the existing `API` constant and `token`):

```javascript
let mode = 'text';
let personImages = []; // array of data URIs

const modeTextBtn = document.getElementById('mode-text');
const modePersonBtn = document.getElementById('mode-person');
const personControls = document.getElementById('person-controls');
const personFiles = document.getElementById('person-files');
const personThumbs = document.getElementById('person-thumbs');

function setMode(m) {
  mode = m;
  modeTextBtn.classList.toggle('active', m === 'text');
  modePersonBtn.classList.toggle('active', m === 'person');
  personControls.style.display = m === 'person' ? 'block' : 'none';
}
modeTextBtn.onclick = () => setMode('text');
modePersonBtn.onclick = () => setMode('person');

function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

personFiles.onchange = async () => {
  const files = Array.from(personFiles.files).slice(0, 4);
  if (personFiles.files.length > 4) {
    alert('Можно максимум 4 фото — возьму первые 4.');
  }
  personImages = await Promise.all(files.map(fileToDataURL));
  personThumbs.innerHTML = personImages
    .map(src => `<img src="${src}" class="thumb">`)
    .join('');
};
```

- [ ] **Step 4: Branch the generate handler by mode**

In the existing generate click handler, before the fetch, branch on `mode`.
Keep the existing text-mode call exactly as-is; add the person branch:

```javascript
if (mode === 'person') {
  if (personImages.length === 0) {
    alert('Загрузи хотя бы одно фото человека.');
    return;
  }
  const resp = await fetch(`${API}/api/generate-person`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({
      prompt: /* existing prompt input value */,
      input_images: personImages,
      count: /* existing count value, or 1 */,
    }),
  });
  // reuse the SAME response handling as text mode (render images, update credits, handle errors)
  return;
}
```

Wire `prompt` and `count` to the same input elements the text mode already uses,
and route the response through the existing render/credits/error code path
(extract it into a shared function if it is currently inline, to avoid
duplication).

- [ ] **Step 5: Manual verification**

The local static server is served from `image-gen/`. Restart if needed:
`cd image-gen && python -m http.server 5500` then open
`http://localhost:5500/login.html`.

Verify:
1. Log in; the generator page shows two mode buttons; text mode works as before.
2. Switch to person mode → file input appears.
3. Select 1 photo → thumbnail shows; Generate → new image of that person appears
   and credit count drops by 1.
4. Selecting 5 photos warns and keeps 4.
5. Generating with 0 photos shows the "load at least one" alert.
6. The result appears in history/gallery.

- [ ] **Step 6: Commit**

```bash
git add image-gen/index.html
git commit -m "feat(image-gen): add person-photo mode (PhotoMaker) to generator UI"
```

---

## Self-Review Notes

- **Spec coverage:** user scenario (toggle + upload + prompt) → Task 3; backend
  function with `img` trigger + SDXL model → Task 1; endpoint with credits/
  validation/history `mode:"person"` → Task 2; error handling (no image, >4,
  402, Runware error via raise_for_status) → Tasks 2 & 3; testing → Tasks 1 & 2
  (auto) and Task 3 (manual). Reference photos not persisted to DB → Task 2
  (only `image_urls` saved). ✓
- **Deferred config:** PhotoMaker model AIR id has a concrete default
  (`civitai:139562@344487`) with a verification step (Task 1, Step 5). Photo
  resize/size-limit from the spec's open questions is intentionally NOT
  implemented yet (YAGNI) — add only if real photos exceed request limits.
- **Type consistency:** `generate_person_images` signature identical across
  runware.py, main.py import, and the mocked test target `main.generate_person_images`. ✓

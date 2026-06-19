# hush-feeds

Pinterest RSS auto-publish feeds for the **Hush** brand (hormone-free menopause
self-care, hushchews.com) — the isolated, GitHub-Pages parity of how `korp-blog`
serves KORP's feeds. Quarry publishes `data/pins-manifest.json` at batch start;
a free daily GitHub Action (`.github/workflows/pin-drip.yml` →
`scripts/build_pin_feeds.py`) releases that day's **started, due** pins into
`docs/feeds/pins-<slug>.xml`, which GitHub Pages serves.

- **Nothing posts until a batch is started** (manual `release N per day`). The
  daily job is gated on `release_date`; un-started pins have none.
- **Feed URL pattern:** `https://<owner>.github.io/hush-feeds/feeds/pins-<slug>.xml`
- **Item links** point to **hushchews.com** (the claimed domain). **Images** are
  Cloudinary URLs. Zero secrets (built-in `GITHUB_TOKEN`).

One-time: make this repo public, enable **Settings → Pages → Deploy from branch
→ `main` / `/docs`**, then connect the feed URL in the Hush Pinterest account
(Settings → Bulk Create Pins → Auto-publish) with **Read and write** workflow
permissions enabled.

## Description

<!-- What does this PR change and why? Link the issue it closes, if any. -->

## Checklist

- [ ] I read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CONTEXT.md`](CONTEXT.md).
- [ ] My commits follow Conventional Commits and carry a `Signed-off-by` trailer
      (`git commit -s`) — DCO.
- [ ] Backend changes: `pytest` passes (`DEPRESS_USE_SQLITE=1 CHANNEL_LAYER=memory pytest -q`).
- [ ] Frontend changes: `npm test` and `npm run build` pass in every app I touched.
- [ ] No code from `apps/mini-app/vendor/**` (GPLv3) was copied into the browser,
      admin, backend, or packages.
- [ ] No secrets, real `.env` values, or other people's content are introduced.
- [ ] `README.md` / docs updated if user-facing behavior or layout changed.

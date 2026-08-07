# Watcher H3 Vast PyWorker

Minimal public Vast PyWorker definition for the Watcher H3 provider-neutral image. It contains no credentials, prompts, media, model weights, or provider receipts.

The paired container must expose `POST /watcher/h3` on port `8000` with `WATCHER_H3_TRANSPORT=vast`. Requests are serialized because one H3 inference owns the GPU. The endpoint and worker group must use `cold_workers=0`; the governed canary uses exactly one test worker.

Vast requires a benchmark before admitting a worker to the ready pool. Supply a
fresh, one-use Watcher H3 request as base64 JSON in
`VAST_H3_BENCHMARK_PAYLOAD_B64`. It runs once with no warmup or concurrency and
must use newly minted input/output URLs. The value is never logged or committed.

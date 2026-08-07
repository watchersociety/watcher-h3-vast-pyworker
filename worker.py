import base64
import binascii
import json
import os

from vastai import BenchmarkConfig, HandlerConfig, LogActionConfig, Worker, WorkerConfig


def video_workload(payload):
    width = float(payload.get("width", 1344))
    height = float(payload.get("height", 768))
    duration = float(payload.get("durationSeconds", 3))
    return width * height * max(1.0, duration * 24.0)


def benchmark_payload():
    """Decode the one-use governed benchmark without logging signed URLs."""
    encoded = os.environ.get("VAST_H3_BENCHMARK_PAYLOAD_B64", "").strip()
    if not encoded:
        raise RuntimeError("VAST_H3_BENCHMARK_PAYLOAD_REQUIRED")
    try:
        payload = json.loads(base64.b64decode(encoded, validate=True))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("VAST_H3_BENCHMARK_PAYLOAD_INVALID") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("VAST_H3_BENCHMARK_PAYLOAD_INVALID")
    return payload


def build_worker():
    port = int(os.environ.get("H3_HTTP_PORT", "8000"))
    return Worker(WorkerConfig(
        model_server_url="http://127.0.0.1",
        model_server_port=port,
        model_log_file=os.environ.get("H3_HTTP_LOG_PATH", "/tmp/watcher-h3-http.log"),
        handlers=[HandlerConfig(
            route="/watcher/h3",
            allow_parallel_requests=False,
            max_queue_time=60.0,
            benchmark_config=BenchmarkConfig(
                generator=benchmark_payload,
                runs=1,
                concurrency=1,
                do_warmup=False,
            ),
            workload_calculator=video_workload,
        )],
        log_action_config=LogActionConfig(
            on_load=["WATCHER_H3_HTTP_READY"],
            on_error=["Traceback (most recent call last):"],
            on_info=[],
        ),
    ))


if __name__ == "__main__":
    build_worker().run()

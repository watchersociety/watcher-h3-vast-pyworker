import os

from vastai import BenchmarkConfig, HandlerConfig, LogActionConfig, Worker, WorkerConfig


REFERENCE_PIXELS = 1344 * 768
DEFAULT_LOAD_UNITS_PER_OUTPUT_SECOND = 4000.0


def video_workload(payload):
    width = float(payload.get("width", 1344))
    height = float(payload.get("height", 768))
    duration = float(payload.get("durationSeconds", 3))
    units_per_second = float(os.environ.get(
        "VAST_H3_LOAD_UNITS_PER_OUTPUT_SECOND",
        str(DEFAULT_LOAD_UNITS_PER_OUTPUT_SECOND),
    ))
    pixel_scale = max(1.0, (width * height) / REFERENCE_PIXELS)
    return pixel_scale * max(1.0, duration) * units_per_second


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
            workload_calculator=video_workload,
        ), HandlerConfig(
            # PyWorker requires one benchmark handler before joining the pool.
            # Qualify the already verified runtime without embedding expiring
            # Watcher URLs or producing an ungoverned video artifact.
            route="/watcher/h3/benchmark",
            allow_parallel_requests=False,
            max_queue_time=60.0,
            benchmark_config=BenchmarkConfig(
                dataset=[{}],
                runs=1,
                concurrency=1,
                do_warmup=False,
            ),
            workload_calculator=lambda _payload: 1.0,
        )],
        log_action_config=LogActionConfig(
            on_load=["WATCHER_H3_HTTP_READY"],
            on_error=["WATCHER_H3_HTTP_ERROR", "Traceback (most recent call last):"],
            on_info=[],
        ),
    ))


if __name__ == "__main__":
    build_worker().run()

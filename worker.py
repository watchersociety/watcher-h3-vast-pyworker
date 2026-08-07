import os

from vastai import HandlerConfig, LogActionConfig, Worker, WorkerConfig


def video_workload(payload):
    width = float(payload.get("width", 1344))
    height = float(payload.get("height", 768))
    duration = float(payload.get("durationSeconds", 3))
    return width * height * max(1.0, duration * 24.0)


port = int(os.environ.get("H3_HTTP_PORT", "8000"))
Worker(WorkerConfig(
    model_server_url="http://127.0.0.1",
    model_server_port=port,
    model_log_file=os.environ.get("H3_HTTP_LOG_PATH", "/tmp/watcher-h3-http.log"),
    handlers=[HandlerConfig(
        route="/watcher/h3",
        allow_parallel_requests=False,
        max_queue_time=60.0,
        workload_calculator=video_workload,
    )],
    log_action_config=LogActionConfig(
        on_load=["WATCHER_H3_HTTP_READY"],
        on_error=["Traceback (most recent call last):"],
        on_info=[],
    ),
)).run()

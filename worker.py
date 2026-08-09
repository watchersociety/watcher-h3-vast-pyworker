import os

from aiohttp import ClientError, ClientSession, ClientTimeout, ContentTypeError, web
from vastai import BenchmarkConfig, HandlerConfig, LogActionConfig, Worker, WorkerConfig


REFERENCE_PIXELS = 1344 * 768
DEFAULT_LOAD_UNITS_PER_OUTPUT_SECOND = 4000.0
HEALTH_ROUTE = "/healthz"
WORKER_CONTRACT = "WatcherH3WorkerContract-v1"


def video_workload(payload):
    width = float(payload.get("width", 1344))
    height = float(payload.get("height", 768))
    duration = float(payload.get("durationSeconds", 3))
    units_per_second = float(os.environ.get(
        "VAST_H3_LOAD_UNITS_PER_OUTPUT_SECOND",
        str(DEFAULT_LOAD_UNITS_PER_OUTPUT_SECOND),
    ))
    return max(1.0, width * height / REFERENCE_PIXELS) * max(1.0, duration) * units_per_second


def make_public_health_handler(internal_health_url):
    async def public_health(_request):
        try:
            async with ClientSession(timeout=ClientTimeout(total=10)) as session:
                async with session.get(internal_health_url) as response:
                    state = await response.json()
                    status = state.get("status") if isinstance(state, dict) else None
                    contract = state.get("contract") if isinstance(state, dict) else None
                    ready = response.status == 200 and status == "ready" and contract == WORKER_CONTRACT
        except (ClientError, ContentTypeError, TimeoutError, ValueError):
            status, contract, ready = None, None, False
        return web.json_response({
            "status": status if status in {"initializing", "ready", "error"} else "unavailable",
            "contract": contract if contract == WORKER_CONTRACT else None,
        }, status=200 if ready else 503)

    return public_health


def build_worker():
    port = int(os.environ.get("H3_HTTP_PORT", "8000"))
    model_server_url = "http://127.0.0.1"
    worker = Worker(WorkerConfig(
        model_server_url=model_server_url,
        model_server_port=port,
        model_log_file=os.environ.get("H3_HTTP_LOG_PATH", "/tmp/watcher-h3-http.log"),
        model_healthcheck_url=HEALTH_ROUTE,
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
    worker.routes.append(web.get(
        HEALTH_ROUTE,
        make_public_health_handler(f"{model_server_url}:{port}{HEALTH_ROUTE}"),
    ))
    return worker


if __name__ == "__main__":
    build_worker().run()

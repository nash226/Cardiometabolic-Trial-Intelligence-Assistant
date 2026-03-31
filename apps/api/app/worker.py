from __future__ import annotations

from .core.config import get_settings


def main() -> None:
    from redis import Redis
    from rq import Connection, SimpleWorker

    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    with Connection(redis):
        # SimpleWorker avoids forking, which is more reliable for local macOS development.
        worker = SimpleWorker([settings.ingestion_queue_name])
        worker.work()


if __name__ == "__main__":
    main()

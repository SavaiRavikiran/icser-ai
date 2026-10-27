"""Entry point: gRPC health server + Event Hubs consumer + Prometheus metrics."""
import asyncio

import grpc
from concurrent import futures
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from src.config import settings
from src.ingestion.event_hubs_consumer import EventHubsConsumer
from src.observability.prometheus_exporter import start_metrics_server
from src.pipeline import run_case
from src.utils.logging import setup_logging


async def process_case(state_dict: dict) -> dict:
    """Process a single (already normalized) ICSR case through the LangGraph pipeline."""
    result = await run_case(state_dict)
    return result["state"]


async def serve():
    """Start gRPC server and Event Hubs consumer."""
    setup_logging(settings.log_level)
    start_metrics_server(settings.prometheus_port)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set("icser-agent", health_pb2.HealthCheckResponse.SERVING)

    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server started on port 50051")

    consumer = EventHubsConsumer(
        connection_string=settings.azure_eventhubs_connection,
        callback=process_case,
    )
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(serve())

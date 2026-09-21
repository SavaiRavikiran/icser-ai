"""Entry point: gRPC server + Event Hubs consumer."""
import asyncio
import grpc
from concurrent import futures
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from src.config import settings
from src.graph.builder import build_icser_graph
from src.ingestion.event_hubs_consumer import EventHubsConsumer
from src.observability.prometheus_exporter import start_metrics_server
from src.utils.logging import setup_logging


async def process_case(state_dict: dict) -> dict:
    """Process a single ICSR case through the LangGraph pipeline."""
    from src.state import ICSRState

    state = ICSRState(**state_dict)
    graph = build_icser_graph()
    result = await graph.ainvoke(state.model_dump())
    return result


def serve():
    """Start gRPC server and Event Hubs consumer."""
    setup_logging(settings.log_level)
    start_metrics_server(settings.prometheus_port)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set("icser-agent", health_pb2.HealthCheckResponse.SERVING)

    server.add_insecure_port("[::]:50051")
    server.start()
    print(f"gRPC server started on port 50051")

    # Start Event Hubs consumer
    consumer = EventHubsConsumer(
        connection_string=settings.azure_eventhubs_connection,
        callback=process_case,
    )
    consumer.start()

    server.wait_for_termination()


if __name__ == "__main__":
    serve()   
"""Azure Event Hubs consumer: receives raw ICSR reports."""
import asyncio
import json
import structlog

from src.ingestion.normalizer import normalize_case
from src.observability.metrics import QUEUE_DEPTH


logger = structlog.get_logger()


class EventHubsConsumer:
    def __init__(self, connection_string: str, callback):
        self.connection_string = connection_string
        self.callback = callback
        self._task: asyncio.Task | None = None

    def start(self) -> asyncio.Task:
        """Start consuming events as a background task on the running event loop."""
        self._task = asyncio.ensure_future(self._consume())
        logger.info("eventhubs_consumer_started")
        return self._task

    async def _consume(self):
        """Main consumption loop (reconnects on error)."""
        from azure.eventhub.aio import EventHubConsumerClient

        while True:
            consumer = EventHubConsumerClient.from_connection_string(
                conn_str=self.connection_string,
                consumer_group="$default",
                eventhub_name="icser-reports",
            )
            try:
                async with consumer:
                    await consumer.receive_batch(
                        on_event_batch=self._on_event_batch,
                        max_batch_size=10,
                        max_wait_time=30,
                        starting_position="@latest",
                    )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("eventhubs_receive_error", error=str(e))
                await asyncio.sleep(5)

    async def _on_event_batch(self, partition_context, events):
        """Handle a batch of events from one partition."""
        if not events:
            return
        QUEUE_DEPTH.set(len(events))
        for event in events:
            await self._process_event(event)
        await partition_context.update_checkpoint()

    async def _process_event(self, event):
        """Process a single Event Hub event."""
        try:
            body = event.body_as_str()
            raw_data = json.loads(body)

            # Normalize to ICSRState-compatible dict
            state = normalize_case(raw_data)
            logger.info(
                "case_received",
                case_id=state.get("case_id"),
                source=state.get("source"),
            )

            # Process through the graph
            result = await self.callback(state)

            logger.info(
                "case_processed",
                case_id=state.get("case_id"),
                status=result.get("submission_status", "unknown"),
                cost_usd=round(result.get("total_cost_usd", 0), 4),
            )

        except Exception as e:
            logger.error("case_processing_error", error=str(e), event_id=getattr(event, "sequence_number", None))   
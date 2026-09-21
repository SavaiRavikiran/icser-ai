"""Azure Event Hubs consumer: receives raw ICSR reports."""
import asyncio
import json
import structlog
from azure.eventhub import EventHubConsumerClient, EventHubConsumerGroup

from src.config import settings
from src.ingestion.normalizer import normalize_case
from src.observability.metrics import QUEUE_DEPTH


logger = structlog.get_logger()


class EventHubsConsumer:
    def __init__(self, connection_string: str, callback):
        self.connection_string = connection_string
        self.callback = callback
        self._task: asyncio.Task | None = None

    def start(self):
        """Start consuming events (blocking)."""
        self._task = asyncio.ensure_future(self._consume())
        logger.info("eventhubs_consumer_started")

    async def _consume(self):
        """Main consumption loop."""
        consumer = EventHubConsumerClient.from_connection_string(
            connection_string=self.connection_string,
            consumer_group="$default",
            eventhub_name="icser-reports",
        )

        async with consumer:
            async with consumer.get_batch_receiver(
                partition_id="0",
                starting_position="-1",  # Latest
            ) as receiver:
                while True:
                    try:
                        events = await receiver.receive_batch(max_message_count=10, timeout_in_seconds=30)
                        if events:
                            QUEUE_DEPTH.set(len(events))
                            for event in events:
                                await self._process_event(event)
                    except Exception as e:
                        logger.error("eventhubs_receive_error", error=str(e))
                        await asyncio.sleep(5)

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
            logger.error("case_processing_error", error=str(e), event_id=event.sequence_number)   
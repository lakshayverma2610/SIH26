import os
import json
import asyncio
import logging
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
RAW_TX_TOPIC = "raw-transactions"
ALERT_TOPIC = "fraud-alerts"

class KafkaStreamingClient:
    def __init__(self):
        self.producer = None
        self.consumer = None
        self._consumer_task = None

    async def start_producer(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        logger.info(f"Kafka Producer connected to {KAFKA_BOOTSTRAP_SERVERS}")

    async def stop_producer(self):
        if self.producer:
            await self.producer.stop()

    async def publish_transaction(self, tx_data: dict):
        if not self.producer:
            await self.start_producer()
        await self.producer.send_and_wait(RAW_TX_TOPIC, tx_data)

    async def start_consumer(self, message_handler):
        self.consumer = AIOKafkaConsumer(
            RAW_TX_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="geo-cashwatch-ai-group",
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset="latest"
        )
        await self.consumer.start()
        logger.info(f"Kafka Consumer connected and listening to {RAW_TX_TOPIC}")
        
        self._consumer_task = asyncio.create_task(self._consume_loop(message_handler))

    async def _consume_loop(self, message_handler):
        try:
            async for msg in self.consumer:
                tx_data = msg.value
                try:
                    await message_handler(tx_data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except asyncio.CancelledError:
            logger.info("Kafka consumer loop cancelled.")
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
        finally:
            await self.stop_consumer()

    async def stop_consumer(self):
        if self.consumer:
            await self.consumer.stop()

kafka_client = KafkaStreamingClient()

import asyncio
import random
import time
import json
import os
from dataclasses import dataclass, asdict
from enum import Enum
from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from typing import Optional, Tuple, Dict, Any
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ====================== Protocol ======================
class CommandType(Enum):
    LOGIN = "Login"
    LOGOFF = "Logoff"
    POSITION = "Position"

@dataclass
class RedisCommand:
    type: CommandType
    player_id: int
    timestamp: int
    
    def serialize(self) -> str:
        data = {
            "type": self.type.value,
            "player_id": self.player_id,
            "timestamp": self.timestamp
        }
        logger.debug(f"Serializing command: {data}")
        return json.dumps(data)

@dataclass
class RedisPositionCommand(RedisCommand):
    position: Tuple[float, float, float]
    
    def __init__(self, player_id: int, position: Tuple[float, float, float]):
        logger.debug(f"Creating position command for bot {player_id}")
        super().__init__(
            type=CommandType.POSITION,
            player_id=player_id,
            timestamp=int(time.time() * 1000)
        )
        self.position = position
    
    def serialize(self) -> str:
        data = asdict(self)
        data['type'] = data['type'].value
        logger.debug(f"Serializing position command: {data}")
        return json.dumps(data)
    
# ====================== Bot Core ======================
@dataclass
class BotMetrics:
    bot_id: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    avg_latency_ms: float = 0.0
    metrics_file: str = ""

    def write_metrics(self):
        """Write metrics to file in a format telegraf can parse"""
        if not self.metrics_file:
            return
        
        metrics_data = {
            "bot_id": self.bot_id,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "avg_latency_ms": self.avg_latency_ms,
            "timestamp": int(time.time() * 1000)
        }

        try:
            with open(self.metrics_file, 'a') as f:
                f.write(json.dumps(metrics_data) + "\n")
        except Exception as e:
            logger.error(f"Failed to write metrics for bot {self.bot_id}: {str(e)}")

class GameBot:
    def __init__(self, bot_id: int, redis_host: str, hz: int = 10, work_dir: str = ""):
        logger.info(f"Initializing bot {bot_id} connecting to {redis_host}")
        self.bot_id = bot_id
        self.redis_host = redis_host
        self.hz = hz
        self.current_position = (random.uniform(0,100), 1, random.uniform(0,100))
        self.redis: Optional[Redis] = None
        self.pubsub: Optional[PubSub] = None
        self.running = False
        self.work_dir = work_dir
        self.metrics = BotMetrics(bot_id=bot_id, metrics_file=os.path.join(self.work_dir, f"bot_{bot_id}_metrics"))

        # Task handles
        self.update_task: Optional[asyncio.Task] = None
        self.listener_task: Optional[asyncio.Task] = None

        # Ensure metrics file exists and is empty at start
        try:
            open(self.metrics.metrics_file, 'w').close()
        except Exception as e:
            logger.error(f"Could not initialize metrics file for bot {bot_id}: {str(e)}")

    async def initialize(self):
        logger.info(f"Bot {self.bot_id} initializing Redis connection")
        try:
            self.redis = await Redis.from_url(self.redis_host)
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe("world:movement")
            await self.redis.sadd("activePlayers", self.bot_id) # type:ignore
            logger.info(f"Bot {self.bot_id} successfully connected to Redis")
        except Exception as e:
            logger.error(f"Bot {self.bot_id} Redis connection failed: {str(e)}")
            raise

    async def start(self):
        logger.info(f"Starting bot {self.bot_id}")
        self.running = True

        self.update_task = asyncio.create_task(self.update_loop())
        self.listener_task = asyncio.create_task(self.listen_loop())
    
    async def listen_loop(self):
        """Listen for messages on subscribed channels and update metrics"""
        logger.info(f"Bot {self.bot_id} listener loop started")
        if not self.pubsub:
            logger.warning(f"Bot {self.bot_id} has no PubSub instance; listener loop exiting")
            return
        try:
            async for message in self.pubsub.listen():
                if message is None:
                    continue
                # We only care about actual messages (ignore subscribe, etc.)
                if message.get('type') == 'message':
                    self.metrics.messages_received += 1
        except asyncio.CancelledError:
            logger.info(f"Bot {self.bot_id} listener loop cancelled")
        except Exception as e:
            logger.error(f"Bot {self.bot_id} error in listener loop: {str(e)}")

    async def update_loop(self):
        logger.info(f"Bot {self.bot_id} update loop started")
        last_metrics_write = time.time()
        metrics_write_interval = 1.0  # seconds

        while self.running:
            try:
                loop_start = time.perf_counter()
                
                # Generate movement
                new_position = (
                    self.current_position[0] + random.uniform(-1,1),
                    1,
                    self.current_position[2] + random.uniform(-1,1)
                )
                logger.debug(f"Bot {self.bot_id} new position: {new_position}")
                
                # Publish update
                cmd = RedisPositionCommand(self.bot_id, new_position)
                if self.redis:
                    await self.redis.publish("world:movement", cmd.serialize())
                    logger.debug(f"Bot {self.bot_id} published update")
                
                # Update metrics
                latency_ms = (time.perf_counter() - loop_start) * 1000
                self.metrics.messages_sent += 1
                self.metrics.avg_latency_ms += (latency_ms - self.metrics.avg_latency_ms) / self.metrics.messages_sent
                logger.debug(f"Bot {self.bot_id} metrics: {self.metrics}")
                
                # Update output file
                current_time = time.time()
                if current_time - last_metrics_write >= metrics_write_interval:
                    self.metrics.write_metrics()
                    last_metrics_write = current_time

                # Throttle if needed
                if self.hz > 0:
                    loop_time = time.perf_counter() - loop_start
                    target_time = 1.0 / self.hz
                    if loop_time < target_time:
                        sleep_time = target_time - loop_time
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.warning(f"Bot {self.bot_id} can't maintain {self.hz}Hz - loop took {loop_time:.4f}s (target: {target_time:.4f}s)")
                    
            except Exception as e:
                logger.error(f"Bot {self.bot_id} error in update loop: {str(e)}")
                await asyncio.sleep(1)

    async def stop(self):
        logger.info(f"Stopping bot {self.bot_id}")
        self.running = False
        # Cancel running tasks
        if self.update_task:
            self.update_task.cancel()
        if self.listener_task:
            self.listener_task.cancel()
        try:
            if self.redis:
                await self.redis.srem("activePlayers", self.bot_id) # type:ignore
                await self.redis.close()
                logger.info(f"Bot {self.bot_id} Redis connection closed")
            if self.pubsub:
                await self.pubsub.close()
        except Exception as e:
            logger.error(f"Bot {self.bot_id} error during shutdown: {str(e)}")

# ====================== Yardstick Integration ======================
async def run_worker(redis_host: str, node_index: int, bots_per_node: int, duration: int, hz: int = 10, work_dir: str = "./"):
    logger.info(f"Starting worker with {bots_per_node} bots on node {node_index}")
    bots = []
    
    try:
        # Initialize all bots
        for i in range(bots_per_node):
            bot_id = node_index * bots_per_node + i
            logger.info(f"Initializing bot {bot_id}")
            bot = GameBot(bot_id, redis_host, hz, work_dir)
            await bot.initialize()
            bots.append(bot)
        
        # Start all bots
        logger.info("Starting all bots")
        start_tasks = [bot.start() for bot in bots]
        await asyncio.gather(*start_tasks)
        
        # Run for duration
        logger.info(f"Running for {duration} seconds")
        await asyncio.sleep(duration)
        
    except Exception as e:
        logger.error(f"Worker error: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("Stopping all bots")
        stop_tasks = [bot.stop() for bot in bots]
        await asyncio.gather(*stop_tasks)
        logger.info("All bots stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    parser.add_argument('--duration', type=float, default=60.0)
    parser.add_argument('--bots', type=int, default=50)
    parser.add_argument('--node-index', type=int, required=True)
    parser.add_argument('--hz', type=int, default=10)
    parser.add_argument('--work-dir', type=str, default="./")
    parser.add_argument('--grid-radius', type=int, default=1, help="Radius of grid area to subscribe to")
    args = parser.parse_args()

    logger.info(f"Starting worker with args: {args}")
    
    try:
        asyncio.run(run_worker(
            redis_host=args.host,
            node_index=args.node_index,
            bots_per_node=args.bots,
            duration=args.duration,
            hz=args.hz,
            work_dir=args.work_dir
        ))
        logger.info("Worker completed successfully.")
    except Exception as e:
        logger.error(f"Worker failed: {str(e)}")
        raise

    logger.info("Worker finished execution")
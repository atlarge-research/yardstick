import asyncio
import random
import time
import json
import os
import math
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Tuple, Dict, Any, Callable, Awaitable, Set
import argparse
import logging
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

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
    
# ====================== Dynamic Pub/Sub ======================
class DynamicPubSub:
    """
    Dynamic area-based pub/sub manager.
    Publishes to and subscribes from channels like: world:movement:<x>:<y>
    """
    def __init__(self, redis_pub: Redis, redis_sub: Redis, grid_radius: int = 1):
        self.redis_pub = redis_pub
        self.redis_sub = redis_sub
        self.pubsub: PubSub = self.redis_sub.pubsub()
        self.grid_radius = grid_radius
        self.current_subs: Set[str] = set()
        self.listen_task: Optional[asyncio.Task] = None

    def channel_name(self, x: int, y: int) -> str:
        return f"world:movement:{x}:{y}"

    async def subscribe_to_area(
        self,
        center_column: Tuple[int, int],
        callback: Callable[[dict], Awaitable[None]]
    ):
        loop_start = time.perf_counter()
        timers: Dict[str, float] = {}

        t0 = time.perf_counter()
        new_subs: Set[str] = set()
        cx, cy = center_column

        for dx in range(-self.grid_radius, self.grid_radius + 1):
            for dy in range(-self.grid_radius, self.grid_radius + 1):
                x, y = cx + dx, cy + dy
                new_subs.add(self.channel_name(x, y))
        timers["channels"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        channels_to_subscribe = list(new_subs - self.current_subs)
        if channels_to_subscribe:
            await self.pubsub.subscribe(*channels_to_subscribe)
        timers[f"subscribe{len(channels_to_subscribe)}"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        channels_to_unsubscribe = list(self.current_subs - new_subs)
        if channels_to_unsubscribe:
            await self.pubsub.unsubscribe(*channels_to_unsubscribe)
        timers["unsubscribe"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        self.current_subs = new_subs
        timers["storing"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        if self.listen_task is None:
            self.listen_task = asyncio.create_task(self.listen_loop(callback))
        timers["listening"] = time.perf_counter() - t0

        loop_elapsed_ms = (time.perf_counter() - loop_start) * 1000
        if loop_elapsed_ms > 5:
            logger.debug(f"Subscribe loop slow: {loop_elapsed_ms:.2f} ms")
            for key, val in timers.items():
                logger.debug(f"  {key:<15}: {val*1000:.2f} ms")

    async def publish(self, center_column: Tuple[int, int], message: str):
        cx, cy = center_column
        channel = self.channel_name(cx, cy)
        await self.redis_pub.publish(channel, message)

    async def listen_loop(self, callback: Callable[[dict], Awaitable[None]]):
        async for message in self.pubsub.listen():
            if message is None:
                continue
            if message.get("type") != "message":
                continue
            # process callback asynchronously to avoid backpressure
            asyncio.create_task(callback(message))  # type: ignore

    async def close(self):
        try:
            await self.pubsub.unsubscribe()
        except Exception:
            pass
        try:
            await self.pubsub.close()
        except Exception:
            pass
        self.current_subs.clear()

# ====================== Bot Core (Dynamic) ======================
@dataclass
class BotMetrics:
    bot_id: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    avg_latency_ms: float = 0.0  # average publish latency
    max_publish_latency_ms: float = 0.0
    metrics_file: str = ""

    def write_metrics(self):
        """Write metrics to file in a format telegraf can parse."""
        if not self.metrics_file:
            return

        metrics_data = {
            "bot_id": self.bot_id,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "avg_latency_ms": self.avg_latency_ms,
            "max_publish_latency_ms": self.max_publish_latency_ms,
            "timestamp": int(time.time() * 1000),
        }

        try:
            with open(self.metrics_file, "a") as f:
                f.write(json.dumps(metrics_data) + "\n")
        except Exception as e:
            logger.error(f"Failed to write metrics for bot {self.bot_id}: {str(e)}")

class DynamicGameBot:
    """
    Dynamic pub/sub game bot that:
     - Publishes movement to column-scoped channels
     - Subscribes dynamically to a radius of nearby columns
     - Tracks publish latency and message counts
    """
    def __init__(self, bot_id: int, redis_host: str, hz: int = 10, work_dir: str = "", grid_radius: int = 1):
        logger.info(f"Initializing dynamic bot {bot_id} connecting to {redis_host}")
        self.bot_id = bot_id
        self.redis_host = redis_host
        self.hz = hz
        self.grid_radius = grid_radius

        # Position: random in a 10x10 chunk area (chunk size 16)
        self.current_position: Tuple[float, float, float] = (
            random.uniform(0, 10 * 16),
            1.0,
            random.uniform(0, 10 * 16),
        )
        self.current_column: Tuple[int, int] = self.get_current_column(self.current_position)

        # Redis connections and dynamic pubsub
        self.redis_pub: Optional[Redis] = None
        self.redis_sub: Optional[Redis] = None
        self.pubsub: Optional[DynamicPubSub] = None

        # Lifecycle
        self.running: bool = False
        self.update_task: Optional[asyncio.Task] = None

        # Metrics and output
        self.work_dir = work_dir
        self.metrics = BotMetrics(
            bot_id=bot_id,
            metrics_file=os.path.join(self.work_dir, f"bot_{bot_id}_metrics"),
        )
        # Initialize metrics file empty
        try:
            open(self.metrics.metrics_file, "w").close()
        except Exception as e:
            logger.error(f"Could not initialize metrics file for bot {bot_id}: {str(e)}")

        # Publish latency tracking
        self._publish_latencies: list[float] = []

    @staticmethod
    def get_current_column(position: Tuple[float, float, float]) -> Tuple[int, int]:
        """Get the grid column (x,z) for a given position; column size is 16."""
        pos_x, _, pos_z = position
        column_size = 16
        x = math.floor(pos_x / column_size)
        z = math.floor(pos_z / column_size)
        return (x, z)

    async def initialize(self):
        logger.info(f"Bot {self.bot_id} initializing Redis connections")
        try:
            self.redis_pub = await Redis.from_url(self.redis_host)
            self.redis_sub = await Redis.from_url(self.redis_host)
            self.pubsub = DynamicPubSub(self.redis_pub, self.redis_sub, grid_radius=self.grid_radius)

            # Subscribe to initial area and start listener internally
            await self.pubsub.subscribe_to_area(self.current_column, self.handle_message)

            # Register
            await self.redis_pub.sadd("activePlayers", self.bot_id)  # type: ignore

            logger.info(f"Bot {self.bot_id} successfully connected")
        except Exception as e:
            logger.error(f"Bot {self.bot_id} Redis connection failed: {str(e)}")
            raise

    async def handle_message(self, message: dict):
        """Handle incoming messages from subscribed dynamic channels."""
        try:
            self.metrics.messages_received += 1
        except Exception as e:
            logger.error(f"Bot {self.bot_id} error handling message: {e}")

    async def start(self):
        logger.info(f"Starting dynamic bot {self.bot_id}")
        self.running = True
        self.update_task = asyncio.create_task(self.update_loop())

    async def update_loop(self):
        logger.info(f"Bot {self.bot_id} update loop started (hz={self.hz}, grid_radius={self.grid_radius})")
        last_metrics_write = time.time()
        metrics_write_interval = 1.0  # seconds

        while self.running:
            try:
                loop_start = time.perf_counter()

                # 1) Movement
                new_position = (
                    self.current_position[0] + random.uniform(-1, 1),
                    1.0,
                    self.current_position[2] + random.uniform(-1, 1),
                )

                # 2) Serialize command
                move_cmd = RedisPositionCommand(self.bot_id, new_position)
                serialized = move_cmd.serialize()

                # 3) Dynamic (re)subscription if we changed columns
                new_column = self.get_current_column(new_position)
                if self.pubsub is not None:
                    if new_column != self.current_column:
                        await self.pubsub.subscribe_to_area(new_column, self.handle_message)
                        self.current_column = new_column

                    # 4) Publish to the column channel and track latency
                    t_pub0 = time.perf_counter()
                    await self.pubsub.publish(new_column, serialized)
                    t_pub_ms = (time.perf_counter() - t_pub0) * 1000.0
                    self._publish_latencies.append(t_pub_ms)
                    self.metrics.max_publish_latency_ms = max(self.metrics.max_publish_latency_ms, t_pub_ms)

                # 5) Bookkeeping
                self.metrics.messages_sent += 1
                self.current_position = new_position

                # 6) Periodic metrics write
                current_time = time.time()
                if current_time - last_metrics_write >= metrics_write_interval:
                    # Compute average publish latency since last write
                    if self._publish_latencies:
                        avg = sum(self._publish_latencies) / len(self._publish_latencies)
                        self.metrics.avg_latency_ms = avg
                        self._publish_latencies.clear()
                    self.metrics.write_metrics()
                    last_metrics_write = current_time

                # 7) Throttle to target Hz if requested
                if self.hz > 0:
                    loop_time = time.perf_counter() - loop_start
                    target_time = 1.0 / self.hz
                    if loop_time < target_time:
                        await asyncio.sleep(target_time - loop_time)
                    else:
                        logger.warning(
                            f"Bot {self.bot_id} can't maintain {self.hz}Hz - loop took {loop_time:.4f}s (target: {target_time:.4f}s)"
                        )

            except asyncio.CancelledError:
                logger.info(f"Bot {self.bot_id} update loop cancelled")
                break
            except Exception as e:
                logger.error(f"Bot {self.bot_id} error in update loop: {str(e)}")
                await asyncio.sleep(1)

    async def stop(self):
        logger.info(f"Stopping bot {self.bot_id}")
        self.running = False

        # Cancel task
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        # Logoff + cleanup
        try:
            if self.redis_pub:
                try:
                    await self.redis_pub.srem("activePlayers", self.bot_id)  # type: ignore
                except Exception as e:
                    logger.error(f"Bot {self.bot_id} error sending logoff: {e}")

            if self.pubsub:
                await self.pubsub.close()

            if self.redis_sub:
                await self.redis_sub.close()
            if self.redis_pub:
                await self.redis_pub.close()
        except Exception as e:
            logger.error(f"Bot {self.bot_id} error during shutdown: {str(e)}")

# ====================== Yardstick Integration ======================
async def run_worker(redis_host: str, node_index: int, bots_per_node: int, duration: int, hz: int = 10, work_dir: str = "./", grid_radius: int = 1):
    logger.info( f"Starting worker on node {node_index} with {bots_per_node} bots | duration={duration}s | hz={hz} | grid_radius={grid_radius}")
    bots = []
    
    try:
        # Initialize all bots
        for i in range(bots_per_node):
            bot_id = node_index * bots_per_node + i
            logger.info(f"Initializing bot {bot_id}")
            bot = DynamicGameBot(bot_id, redis_host, hz, work_dir, grid_radius)
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
            work_dir=args.work_dir,
            grid_radius=args.grid_radius
        ))
        logger.info("Worker completed successfully.")
    except Exception as e:
        logger.error(f"Worker failed: {str(e)}")
        raise

    logger.info("Worker finished execution")
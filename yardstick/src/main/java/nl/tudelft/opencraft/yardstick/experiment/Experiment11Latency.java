package nl.tudelft.opencraft.yardstick.experiment;

import com.typesafe.config.Config;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import nl.tudelft.opencraft.yardstick.Yardstick;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.BotManager;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkLocation;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import org.jetbrains.annotations.NotNull;
import science.atlarge.opencraft.mcprotocollib.data.game.entity.metadata.ItemStack;
import science.atlarge.opencraft.mcprotocollib.data.game.entity.metadata.Position;
import science.atlarge.opencraft.mcprotocollib.data.game.entity.player.Hand;
import science.atlarge.opencraft.mcprotocollib.data.game.entity.player.PlayerAction;
import science.atlarge.opencraft.mcprotocollib.data.game.world.block.BlockChangeRecord;
import science.atlarge.opencraft.mcprotocollib.data.game.world.block.BlockFace;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.player.ClientPlayerActionPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.player.ClientPlayerChangeHeldItemPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.player.ClientPlayerPlaceBlockPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.window.ClientCreativeInventoryActionPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.server.world.ServerBlockChangePacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.server.world.ServerMultiBlockChangePacket;
import science.atlarge.opencraft.packetlib.event.session.ConnectedEvent;
import science.atlarge.opencraft.packetlib.event.session.DisconnectedEvent;
import science.atlarge.opencraft.packetlib.event.session.DisconnectingEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketReceivedEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketSendingEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketSentEvent;
import science.atlarge.opencraft.packetlib.event.session.SessionListener;
import science.atlarge.opencraft.packetlib.packet.Packet;

public class Experiment11Latency extends Experiment {

    private final Random random = new Random(System.currentTimeMillis());

    private BotManager botManager;
    private ScheduledFuture<?> runningBotManager;
    private long packetSent = 0L;
    private boolean waitingForReply = false;
    private int countReceived;
    private int countSent;
    private Position blockPos = null;
    private boolean placedBlock = false;

    private Duration experimentDuration;
    private long startMillis;

    private final SessionListener listener = new SessionListener() {
        @Override
        public void packetReceived(PacketReceivedEvent packetReceivedEvent) {
            synchronized (listener) {
                var packet = packetReceivedEvent.getPacket();
                List<Position> blockPositions = new ArrayList<>();
                if (packet instanceof ServerBlockChangePacket) {
                    var changePacket = ((ServerBlockChangePacket) packet);
                    blockPositions.add(changePacket.getRecord().getPosition());
                }
                if (packet instanceof ServerMultiBlockChangePacket) {
                    var changePacket = ((ServerMultiBlockChangePacket) packet);
                    for (BlockChangeRecord record : changePacket.getRecords()) {
                        blockPositions.add(record.getPosition());
                    }
                }
                if (blockPositions.stream().anyMatch(b -> b.equals(blockPos))) {
                    countReceived++;
                    var duration = System.currentTimeMillis() - packetSent;
                    logger.info(String.format("latency %d ms", duration));
                    waitingForReply = false;
                } else {
                    for (Position blockPosition : blockPositions) {
                        logger.info("expected block at " + blockPos + " but got " + blockPosition);
                    }
                }
            }
        }

        @Override
        public void packetSending(PacketSendingEvent packetSendingEvent) {

        }

        @Override
        public void packetSent(PacketSentEvent packetSentEvent) {

        }

        @Override
        public void connected(ConnectedEvent connectedEvent) {

        }

        @Override
        public void disconnecting(DisconnectingEvent disconnectingEvent) {

        }

        @Override
        public void disconnected(DisconnectedEvent disconnectedEvent) {

        }
    };

    public Experiment11Latency(int nodeID, String address, Config config) {
        super(11, nodeID, address, config, "latency experiment");
        this.startMillis = System.currentTimeMillis();
        this.experimentDuration = config.getDuration("duration");
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info(String.format("latency ping sent %d", countSent));
            logger.info(String.format("latency ping received %d", countReceived));
        }));
    }

    @Override
    protected void before() throws InterruptedException {
        botManager = new BotManager(game);
        int numberOfBots = 2;
        botManager.setPlayerStepIncrease(numberOfBots);
        botManager.setPlayerCountTarget(numberOfBots);
        int secondsBetweenJoin = 5;
        runningBotManager = Yardstick.THREAD_POOL.scheduleAtFixedRate(botManager, 0, secondsBetweenJoin, TimeUnit.SECONDS);
    }

    @Override
    protected void tick() {
        synchronized (listener) {
            var bots = botManager.getConnectedBots();
            if (bots.size() == 2 && !waitingForReply) {
                var botA = bots.get(0);
                var botB = bots.get(1);
                if (!ready(botA, botB)) {
                    return;
                }
                if (!botA.hasListener(listener)) {
                    botA.addListener(listener);
                }
                waitingForReply = true;
                CompletableFuture.delayedExecutor(random.nextInt(TICK_MS + 1), TimeUnit.MILLISECONDS).execute(() -> {
                    packetSent = System.currentTimeMillis();
                    var playerLoc = botB.getPlayer().getLocation().intVector();
                    var placePos = new Position(playerLoc.getX() + 1, playerLoc.getY() - 1, playerLoc.getZ());
                    blockPos = new Position(playerLoc.getX() + 1, playerLoc.getY(), playerLoc.getZ());
                    if (placedBlock) {
                        sendPacket(botB, new ClientPlayerActionPacket(PlayerAction.START_DIGGING, blockPos, BlockFace.DOWN));
                        sendPacket(botB, new ClientPlayerActionPacket(PlayerAction.FINISH_DIGGING, blockPos, BlockFace.DOWN));
                        placedBlock = false;
                    } else {
                        sendPacket(botB, new ClientCreativeInventoryActionPacket(36, new ItemStack(3, 64)));
                        sendPacket(botB, new ClientPlayerChangeHeldItemPacket(0));
                        sendPacket(botB, new ClientPlayerPlaceBlockPacket(
                                placePos,
                                BlockFace.UP, Hand.MAIN_HAND, .5f, 1f, .5f));
                        placedBlock = true;
                    }
                    countSent++;
                });
            }
        }
    }

    private boolean ready(Bot botA, Bot botB) {
        if (!botB.isJoined() || !botA.isJoined()) {
            return false;
        }
        var botALocation = botA.getPlayer().getLocation().intVector();
        var botBLocation = botB.getPlayer().getLocation().intVector();
        try {
            ChunkLocation botAChunk = getChunkFromEntityLocation(botALocation);
            ChunkLocation botBChunk = getChunkFromEntityLocation(botBLocation);
            botA.getWorld().getChunk(botAChunk);
            botA.getWorld().getChunk(botBChunk);
            botB.getWorld().getChunk(botAChunk);
            botB.getWorld().getChunk(botBChunk);
        } catch (ChunkNotLoadedException e) {
            return false;
        }
        return true;
    }

    @NotNull
    private ChunkLocation getChunkFromEntityLocation(Vector3i location) {
        return new ChunkLocation(location.getX() >> 4, location.getZ() >> 4);
    }

    private void sendPacket(Bot bot, Packet packet) {
        bot.getClient().getSession().send(packet);
    }

    @Override
    protected boolean isDone() {
        return this.experimentDuration.getSeconds() > 0
                && System.currentTimeMillis() - this.startMillis > this.experimentDuration.toMillis();
    }

    @Override
    protected void after() {
        runningBotManager.cancel(false);
        botManager.setPlayerCountTarget(0);
        botManager.setPlayerStepDecrease(0);
        botManager.run();
    }
}

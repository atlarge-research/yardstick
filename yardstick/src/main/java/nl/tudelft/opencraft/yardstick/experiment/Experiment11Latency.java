package nl.tudelft.opencraft.yardstick.experiment;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import nl.tudelft.opencraft.yardstick.Yardstick;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.BotManager;
import nl.tudelft.opencraft.yardstick.game.GameFactory;
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

    private BotManager botManager;
    // TODO stop experiment after fixed duration?
    private ScheduledFuture<?> runningBotManager;
    private long packetSent = 0L;
    private boolean waitingForReply = false;
    private int countReceived;
    private int countSent;
    private Position blockPos = null;
    private boolean placedBlock = false;

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

    public Experiment11Latency() {
        super(11, "latency experiment", 17);
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info(String.format("latency ping sent %d", countSent));
            logger.info(String.format("latency ping received %d", countReceived));
        }));
    }

    @Override
    protected void before() throws InterruptedException {
        botManager = new BotManager(new GameFactory().getGame(options.host, options.port, options.gameParams));
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
                if (!botB.isJoined() || !botA.isJoined()) {
                    return;
                }
                if (!botA.hasListener(listener)) {
                    botA.addListener(listener);
                }
                waitingForReply = true;
                packetSent = System.currentTimeMillis();
                var blockLoc = botB.getPlayer().getLocation().add(0, 2, 0).intVector();
                blockPos = new Position(blockLoc.getX(), blockLoc.getY(), blockLoc.getZ());
                if (placedBlock) {
                    sendPacket(botB, new ClientPlayerActionPacket(PlayerAction.START_DIGGING, blockPos, BlockFace.DOWN));
                    sendPacket(botB, new ClientPlayerActionPacket(PlayerAction.FINISH_DIGGING, blockPos, BlockFace.DOWN));
                    placedBlock = false;
                } else {
                    sendPacket(botB, new ClientCreativeInventoryActionPacket(36, new ItemStack(3, 64)));
                    sendPacket(botB, new ClientPlayerChangeHeldItemPacket(0));
                    sendPacket(botB, new ClientPlayerPlaceBlockPacket(
                            blockPos,
                            BlockFace.DOWN, Hand.MAIN_HAND, .5f, .5f, .5f));
                    placedBlock = true;
                }

                countSent++;
            }
        }
    }

    private void sendPacket(Bot bot, Packet packet) {
        bot.getClient().getSession().send(packet);
    }

    @Override
    protected boolean isDone() {
        return false;
    }

    @Override
    protected void after() {

    }
}

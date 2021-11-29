package nl.tudelft.opencraft.yardstick.experiment;

import com.typesafe.config.Config;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.FlyTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class Experiment10GenerationStressTest extends Experiment {

    private final Config behaviorConfig;
    private final List<Bot> botList = Collections.synchronizedList(new ArrayList<>());
    private final Set<Bot> targetSet = Collections.synchronizedSet(new HashSet<>());

    private double angle = 0;
    private double increment;
    private double targetDistance;
    private double botSpeed;

    private long startMillis;
    private Duration experimentDuration;
    private Duration delay;

    public Experiment10GenerationStressTest(int nodeID, GameArchitecture game, Config config) {
        super(9, nodeID, game, "Bots move away from the spawn location");
        this.behaviorConfig = config;
    }

    @Override
    protected void before() {
        int botsTotal = behaviorConfig.getInt("bots");
        this.experimentDuration = behaviorConfig.getDuration("duration");
        this.delay = behaviorConfig.getDuration("startDelay");
        this.botSpeed = behaviorConfig.getDouble("bot-speed");
        this.startMillis = System.currentTimeMillis();
        this.increment = 2 * Math.PI / botsTotal;
        this.targetDistance = ((int) (1000 / TICK_MS) * experimentDuration.getSeconds()) * botSpeed;

        // connect the bots; todo: synchronized?
        for (int i = 0; i < botsTotal; i++) {
            Bot bot = createBot();
            Thread connector = new Thread(newBotConnector(bot));
            connector.setName("Connector-" + bot.getName());
            connector.setDaemon(false);
            connector.start();
            botList.add(bot);
        }
    }

    @Override
    protected void tick() {
        if (System.currentTimeMillis() - startMillis < delay.toMillis()) {
            return;
        }

        synchronized (botList) {
            List<Bot> disconnectedBots = botList.stream()
                    .filter(Bot::hasBeenDisconnected)
                    .collect(Collectors.toList());
            disconnectedBots.forEach(bot -> bot.disconnect("Bot is not connected"));
            if (disconnectedBots.size() > 0) {
                logger.warning("Bots disconnected: "
                        + disconnectedBots.stream().map(Bot::getName).reduce("", (a, b) -> a + ", " + b));
                botList.removeAll(disconnectedBots);
            }
        }

        synchronized (botList) {
            for (Bot bot : botList) {
                botTick(bot);
            }
        }
    }

    private void botTick(Bot bot) {
        if (!bot.isJoined()) {
            return;
        }

        // calculate bot target location if not already done
        if (!targetSet.contains(bot)) {
            // calculate target
            Vector3i startLocation = bot.getPlayer().getLocation().intVector();
            int finalX = (int) Math.floor(targetDistance * Math.cos(angle)) + startLocation.getX();
            int finalZ = (int) Math.floor(targetDistance * Math.sin(angle)) + startLocation.getZ();
            angle += increment;
            Vector3i botTarget = new Vector3i(finalX, FlyTaskExecutor.maxY, finalZ);

            // move bot towards target
            bot.getLogger().info(String.format("Moving bot towards final target (%d, %d)", finalX, finalZ));
            bot.setTaskExecutor(new FlyTaskExecutor(bot, botTarget, botSpeed));
            targetSet.add(bot);
        }

        // disconnect bot if arrived
        TaskExecutor t = bot.getTaskExecutor();
        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            bot.disconnect("Arrived at destination");
        }
    }

    private Runnable newBotConnector(Bot bot) {
        return () -> {
            bot.connect();
            int sleep = 1000;
            int tries = 3;
            while (tries-- > 0 && (bot.getPlayer() == null || !bot.isJoined())) {
                try {
                    Thread.sleep(sleep);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                    break;
                }
            }
            if (!bot.isJoined()) {
                logger.warning("Could not connect bot");
                bot.disconnect("Make sure to close all connections.");
            }
        };
    }

    @Override
    protected Bot createBot() {
        return newBot(UUID.randomUUID().toString().substring(0, 6));
    }

    @Override
    protected boolean isDone() {
        boolean timeUp = System.currentTimeMillis() - this.startMillis > this.experimentDuration.toMillis();
        if (timeUp) {
            return true;
        } else if (botList.size() > 0) {
            boolean allBotsDisconnected;
            synchronized (botList) {
                allBotsDisconnected = botList.stream().allMatch(Bot::hasBeenDisconnected);
            }
            if (allBotsDisconnected) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected void after() {
        for (Bot bot : botList) {
            bot.disconnect("disconnect");
        }
    }
}

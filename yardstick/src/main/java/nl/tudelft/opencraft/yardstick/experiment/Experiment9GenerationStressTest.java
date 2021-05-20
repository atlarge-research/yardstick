package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.FlyTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

public class Experiment9GenerationStressTest extends Experiment {

    private final List<Bot> botList = Collections.synchronizedList(new ArrayList<>());
    private final Set<Bot> targetSet = Collections.synchronizedSet(new HashSet<>());

    private double angle = 0;
    private double increment;
    private double targetDistance;
    private double botSpeed;

    private long startMillis;
    private int durationInSeconds;
    private int delay;

    public Experiment9GenerationStressTest() {
        super(9, "Bots move away from the spawn location");
    }

    @Override
    protected void before() {
        int botsTotal = Integer.parseInt(options.experimentParams.get("bots"));
        this.durationInSeconds = Integer.parseInt(options.experimentParams.getOrDefault("duration", "600"));
        this.delay = Integer.parseInt(options.experimentParams.getOrDefault("delay", "0")) * 1000;
        this.botSpeed = Double.parseDouble(options.experimentParams.getOrDefault("speed", "0.3"));
        this.startMillis = System.currentTimeMillis();
        this.increment = 2 * Math.PI / botsTotal;
        this.targetDistance = ((int) (1000 / TICK_MS) * durationInSeconds) * botSpeed;

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
        if (System.currentTimeMillis() - startMillis < delay) {
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
                logger.warning(String.format("Could not connect bot %s:%d.", options.host, options.port));
                bot.disconnect("Make sure to close all connections.");
            }
        };
    }

    protected Bot createBot() {
        return newBot(UUID.randomUUID().toString().substring(0, 6));
    }

    @Override
    protected boolean isDone() {
        boolean timeUp = System.currentTimeMillis() - this.startMillis > this.durationInSeconds * 1_000;
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

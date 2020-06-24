package nl.tudelft.opencraft.yardstick.experiment;

import java.util.*;
import java.util.stream.Collectors;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.model.BotModel;

public abstract class AbstractModelExperiment extends Experiment {

    private final List<Bot> botList = Collections.synchronizedList(new ArrayList<>());
    private final BotModel model;

    private int botsTotal = 0;
    private long startMillis;
    private int durationInSeconds;
    private int secondsBetweenJoin;
    private int numberOfBotsPerJoin;
    private long lastJoin = System.currentTimeMillis();

    public AbstractModelExperiment(int id, String description, BotModel model) {
        super(id, description);
        this.model = model;
    }

    @Override
    protected void before() {
        this.botsTotal = Integer.parseInt(options.experimentParams.get("bots"));
        this.durationInSeconds = Integer.parseInt(options.experimentParams.getOrDefault("duration", "20000"));
        this.secondsBetweenJoin = Integer.parseInt(options.experimentParams.getOrDefault("joininterval", "5"));
        this.numberOfBotsPerJoin = Integer.parseInt(options.experimentParams.getOrDefault("numbotsperjoin", "1"));
        this.startMillis = System.currentTimeMillis();
    }

    @Override
    protected void tick() {
        synchronized (botList) {
            List<Bot> disconnectedBots = botList.stream()
                    .filter(bot -> bot.hasBeenDisconnected())
                    .collect(Collectors.toList());
            disconnectedBots.forEach(bot -> bot.disconnect("Bot is not connected"));
            if (disconnectedBots.size() > 0) {
                logger.warning("Bots disconnected: "
                        + disconnectedBots.stream().map(Bot::getName).reduce("", (a, b) -> a + ", " + b));
                botList.removeAll(disconnectedBots);
            }
        }

        if (System.currentTimeMillis() - this.lastJoin > secondsBetweenJoin * 1000
                && botList.size() <= this.botsTotal) {
            lastJoin = System.currentTimeMillis();
            int botsToConnect = Math.min(this.numberOfBotsPerJoin, this.botsTotal - botList.size());
            for (int i = 0; i < botsToConnect; i++) {
                Bot bot = createBot();
                Thread connector = new Thread(newBotConnector(bot));
                connector.setName("Connector-" + bot.getName());
                connector.setDaemon(false);
                connector.start();
                botList.add(bot);
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

        TaskExecutor t = bot.getTaskExecutor();
        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            bot.setTaskExecutor(model.newTask(bot));
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

package nl.tudelft.opencraft.yardstick.experiment;

import java.util.*;
import java.util.stream.Collectors;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.world.ConnectException;
import nl.tudelft.opencraft.yardstick.util.Vector3d;

public class Experiment5BreakBlock extends Experiment {

    private final List<Bot> botList = Collections.synchronizedList(new ArrayList<>());
    private final BotModel model = new BotModel();

    private int botsTotal = 0;
    private long startMillis;
    private int durationInSeconds;
    private int secondsBetweenJoin;
    private int numberOfBotsPerJoin;
    private final Map<Bot, Vector3d> botSpawnLocations = new HashMap<>();
    private long lastJoin = System.currentTimeMillis();

    public Experiment5BreakBlock() {
        super(5, "Bots join at a regular interval, walk around, and have a chance of breaking a couple of blocks.");
    }

    @Override
    protected void before() {
        this.botsTotal = Integer.parseInt(options.experimentParams.get("bots"));
        this.durationInSeconds = Integer.parseInt(options.experimentParams.getOrDefault("duration", "600"));
        this.secondsBetweenJoin = Integer.parseInt(options.experimentParams.getOrDefault("joininterval", "1"));
        this.numberOfBotsPerJoin = Integer.parseInt(options.experimentParams.getOrDefault("numbotsperjoin", "1"));
        this.startMillis = System.currentTimeMillis();
    }

    @Override
    protected void tick() {
        synchronized (botList) {
            List<Bot> disconnectedBots = botList.stream()
                    .filter(bot -> !bot.isConnected())
                    .collect(Collectors.toList());
            disconnectedBots.forEach(bot -> bot.disconnect("Bot is not connected"));
            botList.removeAll(disconnectedBots);
        }

        if (System.currentTimeMillis() - this.lastJoin > secondsBetweenJoin * 1000
                && botList.size() <= this.botsTotal) {
            lastJoin = System.currentTimeMillis();
            int botsToConnect = Math.min(this.numberOfBotsPerJoin, this.botsTotal - botList.size());
            for (int i = 0; i < botsToConnect; i++) {
                new Thread(() -> {
                    Bot bot;
                    try {
                        bot = createBot();
                    } catch (ConnectException e) {
                        logger.warning(String.format("Could not connect bot %s on part %d.", options.host, options.port));
                        return;
                    }
                    botSpawnLocations.put(bot, bot.getPlayer().getLocation());
                    botList.add(bot);
                }).start();
            }
        }
        synchronized (botList) {
            for (Bot bot : botList) {
                botTick(bot);
            }
        }
    }

    private void botTick(Bot bot) {
        Task t = bot.getTask();
        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            bot.setTask(model.nextTask(bot));
        }
    }

    private Bot createBot() throws ConnectException {
        Bot bot = newBot(UUID.randomUUID().toString().substring(0, 6));
        bot.connect();
        int sleep = 1000;
        int tries = 10;
        while (tries-- > 0 && (bot.getPlayer() == null || !bot.isJoined())) {
            try {
                Thread.sleep(sleep);
            } catch (InterruptedException e) {
                e.printStackTrace();
                break;
            }
        }
        if (!bot.isJoined()) {
            bot.disconnect("Make sure to close all connections.");
            throw new ConnectException();
        }
        return bot;
    }

    @Override
    protected boolean isDone() {

        boolean timeUp = System.currentTimeMillis() - this.startMillis > this.durationInSeconds * 1_000;
        if (timeUp) {
            return true;
        } else if (botList.size() > 0) {
            boolean allBotsDisconnected;
            synchronized (botList) {
                allBotsDisconnected = botList.stream().noneMatch(Bot::isJoined);
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

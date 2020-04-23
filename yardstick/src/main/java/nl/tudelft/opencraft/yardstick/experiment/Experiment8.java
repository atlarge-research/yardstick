package nl.tudelft.opencraft.yardstick.experiment;

import com.github.steveice10.mc.auth.exception.request.RequestException;
import com.github.steveice10.mc.protocol.packet.ingame.client.ClientChatPacket;
import com.github.steveice10.packetlib.Client;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.world.ConnectException;
import nl.tudelft.opencraft.yardstick.model.BotModel;
import nl.tudelft.opencraft.yardstick.model.SimpleMovementModel;
import nl.tudelft.opencraft.yardstick.util.Vector3d;

import java.util.*;
import java.util.stream.Collectors;

public class Experiment8 extends Experiment {

    public static final long EXPERIMENT_DURATION = 10000;
    //
    private Client client;
    private Bot bot;
    private boolean done = false;
    public int tickCounter = 0;
    public static final Scanner cmdScanner = new Scanner(System.in);
    //
    private final List<Bot> botList = Collections.synchronizedList(new ArrayList<>());

    private int botsTotal = 0;
    private int currentBots = 0;
    private long startMillis;
    private int durationInSeconds;
    private int secondsBetweenJoin;
    private int numberOfBotsPerJoin;
    private long lastJoin = System.currentTimeMillis();

    public Experiment8() {
        super(8,
                "Bot listens to commands and gathers data. ");
    }

    @Override
    protected void before() {
        this.botsTotal = Integer.parseInt(options.experimentParams.getOrDefault("bots","2"));

    }

    @Override
    protected void tick() {
        while (botList.size()<botsTotal) {
            synchronized (botList) {
                try {
                    this.bot = newBot("YSBot-" + (botList.size()+1));
                    botList.add(bot);
                } catch (RequestException e) {
                    logger.severe("Could not connect bot. Stopping experiment.");
                    this.done = true;
                    return;
                }
            }
        }
        synchronized (botList){
            for (Bot bot: botList){
                if(!bot.isConnected()) {
                    bot.connect();
                    logger.info("Connected: " + bot.getName());
                }
            }
        }
        synchronized (botList) {
            for (Bot bot : botList) {
                botTick(bot);
            }
        }
    }

    private void botTick(Bot bot) {
        // have the bot spam some stupid stuff
        String spam = null;
        spam = cmdScanner.nextLine();
        //setup case for bot commands?
        if (spam != null) {
            this.bot.getClient().getSession().send(new ClientChatPacket(spam));
            spam = null;
        }
    }

    @Override
    protected void after() {
        client.getSession().disconnect("disconnect");
    }

    @Override
    public boolean isDone() {
        return done;// || !client.getSession().isConnected();
    }

}
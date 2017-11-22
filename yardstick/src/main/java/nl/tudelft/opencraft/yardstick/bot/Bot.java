package nl.tudelft.opencraft.yardstick.bot;

import com.github.steveice10.mc.protocol.MinecraftProtocol;
import com.github.steveice10.packetlib.Client;
import com.github.steveice10.packetlib.event.session.SessionListener;
import com.github.steveice10.packetlib.tcp.TcpSessionFactory;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar.SimpleAStar;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar.heuristic.EuclideanHeuristic;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;
import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.world.SimpleWorldPhysics;
import nl.tudelft.opencraft.yardstick.bot.world.World;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;

public class Bot {

    private final SubLogger logger;
    private final MinecraftProtocol protocol;
    private final String name;
    private final BotTicker ticker;
    private final Client client;
    private final BotController controller;
    //
    private World world;
    private Server server;
    private BotPlayer player;
    private SimpleAStar pathFinder;
    private Task task;

    public Bot(MinecraftProtocol protocol, String host, int port) {
        this.name = protocol.getProfile().getName();
        this.logger = GlobalLogger.getLogger().newSubLogger("Bot").newSubLogger(name);
        this.protocol = protocol;
        this.ticker = new BotTicker(this);
        this.client = new Client(host, port, protocol, new TcpSessionFactory());
        this.client.getSession().addListener(new BotListener(this));
        this.controller = new BotController(this);
    }

    public void addSessionListener(SessionListener... listeners) {
        for (SessionListener listener : listeners) {
            this.client.getSession().addListener(listener);
        }
    }

    public void connect() {
        if (client != null && client.getSession().isConnected()) {
            throw new IllegalStateException("Can not start connection. Bot already isConnected!");
        }
        client.getSession().connect();
        ticker.start();
    }

    public boolean isConnected() {
        return this.client != null
                && this.getClient().getSession() != null
                && this.getClient().getSession().isConnected();
    }

    public boolean isJoined() {
        return isConnected()
                && this.getPlayer() != null
                && this.getPlayer().getLocation() != null;
    }

    public void disconnect(String reason) {
        if (this.ticker != null) {
            this.ticker.stop();
        }
        if (this.task != null) {
            this.task.stop();
        }
        if (this.isJoined()) {
            client.getSession().disconnect(reason);
        }
    }

    public void setTask(Task activity) {
        if (this.task != null) {
            this.task.stop();
        }
        this.task = activity;
    }

    public Task getTask() {
        return this.task;
    }

    public SubLogger getLogger() {
        return logger;
    }

    public SimpleAStar getPathFinder() {
        return pathFinder;
    }

    public MinecraftProtocol getProtocol() {
        return protocol;
    }

    public String getName() {
        return name;
    }

    public Client getClient() {
        return client;
    }

    public BotController getController() {
        return controller;
    }

    public World getWorld() {
        return world;
    }

    public Server getServer() {
        return server;
    }

    public BotPlayer getPlayer() {
        return player;
    }

    public void setWorld(World world) {
        this.world = world;
        // TODO: This shouldn't go here
        if (this.pathFinder == null) {
            this.pathFinder = new SimpleAStar(new EuclideanHeuristic(), new SimpleWorldPhysics(world));
        }
    }

    public void setServer(Server server) {
        this.server = server;
    }

    public void setPlayer(BotPlayer player) {
        this.player = player;
    }
}

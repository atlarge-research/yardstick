package nl.tudelft.opencraft.yardstick.bot;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.github.steveice10.mc.protocol.MinecraftProtocol;
import com.github.steveice10.mc.protocol.data.game.PlayerListEntry;
import com.github.steveice10.packetlib.Client;
import com.github.steveice10.packetlib.event.session.DisconnectedEvent;
import com.github.steveice10.packetlib.event.session.SessionAdapter;
import com.github.steveice10.packetlib.event.session.SessionListener;
import com.github.steveice10.packetlib.tcp.TcpSessionFactory;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar.SimpleAStar;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar.heuristic.EuclideanHeuristic;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.world.SimpleWorldPhysics;
import nl.tudelft.opencraft.yardstick.bot.world.World;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;

import java.util.UUID;
/**
 * Represents a Minecraft simulated bot.
 */
public class Bot {

    @JsonIgnore
    private final SubLogger logger;
    @JsonIgnore
    private final MinecraftProtocol protocol;
    private final String name;
    @JsonIgnore
    private final BotTicker ticker;
    @JsonIgnore
    private final Client client;
    @JsonIgnore
    private final BotController controller;
    //
    private boolean disconnected = false;
    @JsonIgnore
    private World world;
    @JsonIgnore
    private Server server;
    private BotPlayer player;
    @JsonIgnore
    private SimpleAStar pathFinder;
    private TaskExecutor taskExecutor;
    private PlayerListEntry[] players;
    private UUID following;
    private String target;
    private boolean teleport;

    /**
     * Creates a new bot with the given {@link MinecraftProtocol}.
     *
     * @param protocol the protocol.
     * @param host the hostname of the Minecraft server.
     * @param port the port of the Minecraft server.
     */
    public Bot(MinecraftProtocol protocol, String host, int port) {

        this.name = protocol.getProfile().getName();
        this.logger = GlobalLogger.getLogger().newSubLogger("Bot").newSubLogger(name);

        this.protocol = protocol;
        this.ticker = new BotTicker(this);
        this.client = new Client(host, port, protocol, new TcpSessionFactory());
        this.client.getSession().addListener(new BotDataGatherer(this));
        this.controller = new BotController(this);
        this.teleport = false;
        // Set disconnected field
        this.client.getSession().addListener(new SessionAdapter() {
            @Override
            public void disconnected(DisconnectedEvent event) {
                disconnected = true;
            }
        });
    }

    /**
     * Adds sessionlisteners to the {@link Client} of the bot.
     *
     * @param listeners the listeners.
     */
    public void addSessionListener(SessionListener... listeners) {
        for (SessionListener listener : listeners) {
            this.client.getSession().addListener(listener);
        }
    }

    /**
     * Connects the bot to the Minecraft server.
     *
     * @throws IllegalStateException if the bot is already connected.
     */
    public void connect() {
        if (client.getSession().isConnected()) {
            throw new IllegalStateException("Can not start connection. Bot already isConnected!");
        }
        client.getSession().connect();
        ticker.start();
    }

    /**
     * Returns true if the bot is connected to the server.
     *
     * @return true if connected.
     */
    public boolean isConnected() {
        return this.client != null
                && this.getClient().getSession() != null
                && this.getClient().getSession().isConnected();
    }

    /**
     * Returns true if the bot has been disconnected from the server at some
     * point.
     *
     * @return true if disconnected.
     */
    public boolean hasBeenDisconnected() {
        return disconnected;
    }

    /**
     * Returns true if the bot has received player and player location data.
     *
     * @return true if the bot has data.
     */
    public boolean isJoined() {
        return isConnected()
                && this.getPlayer() != null
                && this.getPlayer().getLocation() != null;
    }

    /**
     * Disconnects the bot for the given reason.
     *
     * @param reason the reason.
     */
    public void disconnect(String reason) {
        if (this.ticker != null) {
            this.ticker.stop();
        }
        if (this.taskExecutor != null) {
            this.taskExecutor.stop();
        }
        if (this.isJoined()) {
            client.getSession().disconnect(reason);
        }
        disconnected = true;
    }

    /**
     * Sets the current task of the bot.
     *
     * @param activity the task.
     */
    public void setTaskExecutor(TaskExecutor activity) {
        if (this.taskExecutor != null) {
            this.taskExecutor.stop();
        }
        this.taskExecutor = activity;
    }

    /**
     * Returns the bot's current task.
     *
     * @return the task.
     */
    public TaskExecutor getTaskExecutor() {
        return this.taskExecutor;
    }

    /**
     * Returns the logger of this bot. This will be null if the world has not
     * been set.
     *
     * @return the logger.
     */
    public SubLogger getLogger() {
        return logger;
    }

    /**
     * Returns the pathfinder for this bot.
     *
     * @return the path finder.
     */
    public SimpleAStar getPathFinder() {
        return pathFinder;
    }

    /**
     * Returns the protocol for this bot.
     *
     * @return the protocol.
     */
    public MinecraftProtocol getProtocol() {
        return protocol;
    }

    /**
     * Returns the name of this bot.
     *
     * @return the name.
     */
    public String getName() {
        return name;
    }

    /**
     * Returns the client of this bot.
     *
     * @return the client.
     */
    public Client getClient() {
        return client;
    }

    /**
     * Returns the bot controller of this bot.
     *
     * @return the controller.
     */
    public BotController getController() {
        return controller;
    }

    /**
     * Returns the world data of this bot.
     *
     * @return the world data.
     */
    public World getWorld() {
        return world;
    }

    /**
     * Returns the server data of this bot.
     *
     * @return the server data.
     */
    public Server getServer() {
        return server;
    }

    /**
     * Returns the player data of this bot.
     *
     * @return the player data.
     */
    public BotPlayer getPlayer() {
        return player;
    }

    /**
     * Sets the world data and initiates a pathfinder for the world.
     *
     * @param world the world.
     */
    public void setWorld(World world) {
        this.world = world;
        // TODO: This shouldn't go here
        if (this.pathFinder == null) {
            this.pathFinder = new SimpleAStar(new EuclideanHeuristic(), new SimpleWorldPhysics(world));
        }
    }

    /**
     * Sets the server data for the bot.
     *
     * @param server the server.
     */
    public void setServer(Server server) {
        this.server = server;
    }

    /**
     * Sets the player data for the bot.
     *
     * @param player the player.
     */
    public void setPlayer(BotPlayer player) {
        this.player = player;
    }

    /**
     * Flagging bots for teleporting
     */
    public void setTeleport(){teleport = !teleport;}
    public boolean getTeleport(){return this.teleport;}

    public void setPlayerSize(int s){ this.players = new PlayerListEntry[s]; }

    public void addPlayers(PlayerListEntry ple){
        //check for no duplicate entries
        if(dupCheck(ple)) {
            for (int i = 0; i < players.length; i++) {
                if (players[i] == null) {
                    this.players[i] = ple;
                    break;
                }
            }
        }
    }
    public boolean dupCheck(PlayerListEntry ple){
        for (PlayerListEntry pl : players){
            if(pl != null && pl.getProfile().getId().equals(ple.getProfile().getId())){
                return false;
            }
        }
        return true;
    }

    public void remPlayers(PlayerListEntry ple){
        for (int i = 0; i < players.length; i++){
            if(players[i] != null && players[i].getProfile().getId().equals(ple.getProfile().getId())){
                this.players[i] = null;
            }
        }
    }

    public PlayerListEntry[] getPlayers(){ return this.players; }

    public UUID getFollowing() { return following; }
    public String getFollowingName() { return target; }
    /**
     * Set target for bot to follow
     */
    public void setFollowing(UUID uuid, String name) { this.following = uuid; this.target = name; }
}

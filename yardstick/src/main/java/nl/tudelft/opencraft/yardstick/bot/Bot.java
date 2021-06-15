/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2020 AtLarge Research
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

package nl.tudelft.opencraft.yardstick.bot;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.github.steveice10.mc.protocol.ClientListener;
import com.github.steveice10.mc.protocol.MinecraftProtocol;
import com.github.steveice10.mc.protocol.data.SubProtocol;
import com.github.steveice10.packetlib.ProxyInfo;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.FixedCircle;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar.SimpleAStar;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar.heuristic.EuclideanHeuristic;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.world.SimpleWorldPhysics;
import nl.tudelft.opencraft.yardstick.bot.world.World;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import com.github.steveice10.packetlib.Client;
import com.github.steveice10.packetlib.event.session.DisconnectedEvent;
import com.github.steveice10.packetlib.event.session.SessionAdapter;
import com.github.steveice10.packetlib.event.session.SessionListener;
import com.github.steveice10.packetlib.tcp.TcpSessionFactory;

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
    private FixedCircle fixedCircle;
    private TaskExecutor taskExecutor;

    /**
     * Creates a new bot with the given {@link MinecraftProtocol}.
     *
     * @param protocol the protocol.
     * @param host     the hostname of the Minecraft server.
     * @param port     the port of the Minecraft server.
     */
    public Bot(MinecraftProtocol protocol, String host, int port) {
        this(protocol, new Client(host, port, protocol, new TcpSessionFactory(null)));
    }

    /**
     * Creates a new bot with the given {@link MinecraftProtocol} and {@link Client}.
     *
     * @param protocol the protocol.
     * @param client   the Minecraft client.
     */
    public Bot(MinecraftProtocol protocol, Client client) {
        this.name = protocol.getProfile().getName();
        this.logger = GlobalLogger.getLogger().newSubLogger("Bot").newSubLogger(name);
        this.protocol = protocol;
        this.ticker = new BotTicker(this);
        this.client = client;
        this.client.getSession().addListener(new BotListener(this));
        this.controller = new BotController(this);

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

    public FixedCircle getFixedCircle(){return fixedCircle;}

    public void setFixedCircle(FixedCircle toSet){this.fixedCircle=toSet;}
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
}

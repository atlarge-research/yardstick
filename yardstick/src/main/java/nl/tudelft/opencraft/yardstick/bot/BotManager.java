package nl.tudelft.opencraft.yardstick.bot;

import java.net.InetSocketAddress;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import lombok.Getter;
import lombok.Setter;
import net.jodah.failsafe.Failsafe;
import net.jodah.failsafe.Policy;
import net.jodah.failsafe.RetryPolicy;
import nl.tudelft.opencraft.yardstick.Yardstick;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;
import nl.tudelft.opencraft.yardstick.game.SingleServer;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import org.apache.commons.collections4.list.UnmodifiableList;
import science.atlarge.opencraft.mcprotocollib.MinecraftProtocol;

/**
 * Connects the specified number of bots to the game server
 * <p>
 * The BotManager implements runnable and should be invoked at a fixed frequency to monitor the number of players in the game.
 */
public class BotManager implements Runnable {

    private final SubLogger logger = GlobalLogger.getLogger().newSubLogger(BotManager.class.getSimpleName());

    @Getter
    @Setter
    private int playerCountTarget = 0;
    @Getter
    @Setter
    private int playerStepIncrease = 0;
    @Getter
    @Setter
    private int playerStepDecrease = 0;
    @Getter
    private final GameArchitecture game;
    private final List<Bot> connectedBots = Collections.synchronizedList(new ArrayList<>());
    private final List<Future<Bot>> connectingBots = Collections.synchronizedList(new ArrayList<>());
    private final Policy<Bot> retryPolicy = new RetryPolicy<Bot>()
            .handleResultIf(b -> !b.isConnected())
            .withMaxAttempts(-1)
            .withDelay(Duration.ofSeconds(5))
            .withMaxDuration(Duration.ofSeconds(60));

    public static void main(String[] args) throws InterruptedException {
        var a = Yardstick.LOGGER;
        var addr = new InetSocketAddress("::1", 25565);
        var botmanager = new BotManager(new SingleServer(addr), 2, 2, 1);
        Yardstick.THREAD_POOL.scheduleAtFixedRate(botmanager, 0, 5, TimeUnit.SECONDS);
    }

    public BotManager(GameArchitecture game, int playerCountTarget, int playerStepIncrease, int playerStepDecrease) {
        this.playerCountTarget = playerCountTarget;
        this.playerStepIncrease = playerStepIncrease;
        this.playerStepDecrease = playerStepDecrease;
        this.game = game;
    }

    public BotManager(GameArchitecture game) {
        this.game = game;
    }

    public void setPlayerCountTarget(int playerCountTarget) {
        this.playerCountTarget = playerCountTarget;
    }

    public List<Bot> getConnectedBots() {
        synchronized (connectedBots) {
            return UnmodifiableList.unmodifiableList(new ArrayList<>(connectedBots));
        }
    }

    @Override
    public void run() {
        connectedBots.removeIf(b -> !b.isConnected());
        connectingBots.removeIf(Future::isDone);

        int playerCount = getPlayerCount();
        int playerDeficit = playerCountTarget - playerCount;
        int playerSurplus = -playerDeficit;
        if (playerCount < playerCountTarget) {
            int numPlayersToConnect = playerStepIncrease < 1 ? playerDeficit : Math.min(playerStepIncrease, playerDeficit);
            for (int i = 0; i < numPlayersToConnect; i++) {
                var username = UUID.randomUUID().toString().substring(0, 8);
                connectingBots.add(game.getAddressForPlayer().thenApply(a -> Failsafe.with(retryPolicy).get(() -> {
                    Bot bot = new Bot(new MinecraftProtocol(username), a.getHostName(), a.getPort());
                    bot.connect();
                    return bot;
                })).whenComplete((bot, ex) -> {
                    if (ex != null) {
                        logger.log(Level.WARNING, ex.getMessage(), ex);
                    } else {
                        connectedBots.add(bot);
                    }
                }));
            }
        } else if (playerCount > playerCountTarget && connectedBots.size() > 0) {
            int numPlayersToDisconnect = playerStepDecrease < 1 ? playerSurplus : Math.min(playerStepDecrease, playerSurplus);
            for (int i = 0; i < numPlayersToDisconnect; i++) {
                connectedBots.remove(0).disconnect(String.format("Too many players connected. Is %d, should be %d", playerCount, playerCountTarget));
            }
        }
    }

    private int getPlayerCount() {
        return connectedBots.size() + connectingBots.size();
    }
}

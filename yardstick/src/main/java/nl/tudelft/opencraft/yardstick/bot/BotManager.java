package nl.tudelft.opencraft.yardstick.bot;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Future;
import java.util.logging.Level;
import lombok.Getter;
import lombok.Setter;
import net.jodah.failsafe.Failsafe;
import net.jodah.failsafe.Policy;
import net.jodah.failsafe.RetryPolicy;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;

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
    @Getter
    private final List<Bot> connectedBots = new ArrayList<>();
    private final List<Future<Bot>> connectingBots = Collections.synchronizedList(new ArrayList<>());
    private final Policy<Object> retryPolicy = new RetryPolicy<>().withMaxAttempts(3).withMaxDuration(Duration.ofSeconds(60));

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

    @Override
    public void run() {
        connectedBots.removeIf(b -> !b.isConnected());
        connectingBots.removeIf(Future::isDone);

        int playerCount = getPlayerCount();
        int playerDeficit = playerCountTarget - playerCount;
        if (playerCount < playerCountTarget) {
            int numPlayersToConnect = playerStepIncrease < 1 ? playerDeficit : Math.min(playerStepIncrease, playerDeficit);
            for (int i = 0; i < numPlayersToConnect; i++) {
                connectingBots.add(Failsafe.with(retryPolicy).getAsync(() -> {
                    // FIXME
                    Bot bot = new Bot(null, null, 0);
                    bot.connect();
                    connectedBots.add(bot);
                    return bot;
                }).whenComplete((b, ex) -> {
                    if (ex != null) {
                        logger.log(Level.WARNING, ex.getMessage(), ex);
                    }
                }));
            }
        } else if (playerCount > playerCountTarget) {
            int numPlayersToDisconnect = playerStepDecrease < 1 ? playerDeficit : Math.min(playerStepDecrease, playerDeficit);
            for (int i = 0; i < numPlayersToDisconnect; i++) {
                connectedBots.remove(0).disconnect(String.format("Too many players connected. Is %d should be %d", playerCount, playerCountTarget));
            }
        }
    }

    private int getPlayerCount() {
        return connectedBots.size() + connectingBots.size();
    }
}

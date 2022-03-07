package nl.tudelft.opencraft.yardstick.game;

import com.typesafe.config.Config;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;

import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URISyntaxException;
import java.text.MessageFormat;
import java.util.Objects;

public class GameFactory {

    private final SubLogger logger = GlobalLogger.getLogger().newSubLogger("Bot").newSubLogger(GameFactory.class.getSimpleName());

    public GameArchitecture getGame(String address, Config config) {
        Objects.requireNonNull(address);
        GameArchitecture res;
        try {
            String architecture = config.getString("game-architecture");
            if (architecture.equals("servo")) {
                res = new ServerlessHttpGame(new URI(address));
            } else { // assuming single server
                var parts = address.split(":");
                var host = parts[0];
                var port = Integer.parseInt(parts[1]);
                res = new SingleServer(new InetSocketAddress(host, port));
            }
            logger.info(MessageFormat.format("created game {0} based on architecture ''{1}''",
                    res.getClass().getSimpleName(), architecture));
        } catch (URISyntaxException e) {
            throw new RuntimeException(e);
        }
        return res;
    }
}

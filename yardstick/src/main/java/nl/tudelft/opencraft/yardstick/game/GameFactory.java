package nl.tudelft.opencraft.yardstick.game;

import com.typesafe.config.Config;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.Objects;

public class GameFactory {

    private final Logger logger = LoggerFactory.getLogger(GameFactory.class);

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
            logger.info("created game {} based on architecture ''{}''",
                    res.getClass().getSimpleName(), architecture);
        } catch (URISyntaxException e) {
            throw new RuntimeException(e);
        }
        return res;
    }
}

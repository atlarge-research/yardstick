package nl.tudelft.opencraft.yardstick.game;

import com.typesafe.config.Config;
import java.net.URI;
import java.util.Objects;

public class GameFactory {
    public GameArchitecture getGame(String host, int port, Config config) {
        String architecture = config.getString("game-architecture");
        if (!architecture.isBlank()) {
            if (architecture.equals("servo")) {
                Objects.requireNonNull(host);
                URI uri = URI.create(String.format("https://%s:%d", host, port));
                return new ServerlessHttpGame(uri);
            }
        }
        return new SingleServer(host, port);
    }
}

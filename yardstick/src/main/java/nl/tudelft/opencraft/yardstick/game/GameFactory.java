package nl.tudelft.opencraft.yardstick.game;

import com.typesafe.config.Config;
import java.net.URI;
import java.util.Objects;

public class GameFactory {
    public GameArchitecture getGame(String host, int port, Config config) {
        String architecture = config.getString("game-architecture");
        if (!architecture.isBlank()) {
            if (architecture.equals("serverless-aws-sdk")) {
                config = config.getConfig(architecture);
                String functionName = config.getString("functionName");
                String region = config.getString("region");
                Objects.requireNonNull(functionName);
                Objects.requireNonNull(region);
                return new ServerlessAwsSdkGame(functionName, region);
            } else if (architecture.equals("serverless-http")) {
                Objects.requireNonNull(host);
                URI uri = URI.create(String.format("https://%s:%d", host, port));
                return new ServerlessHttpGame(uri);
            }
        }
        return new SingleServer(host, port);
    }
}

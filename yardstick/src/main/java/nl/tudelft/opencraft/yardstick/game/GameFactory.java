package nl.tudelft.opencraft.yardstick.game;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.Map;
import java.util.Objects;

public class GameFactory {
    public GameArchitecture getGame(String host, int port, Map<String, String> gameParams) {
        if (gameParams.containsKey("architecture")) {
            String archi = gameParams.get("architecture");
            if (archi.equals("serverless-aws-sdk")) {
                String functionName = gameParams.get("functionName");
                String region = gameParams.get("region");
                Objects.requireNonNull(functionName);
                Objects.requireNonNull(region);
                return new ServerlessAwsSdkGame(functionName, region);
            } else if (archi.equals("serverless-http")) {
                Objects.requireNonNull(host);
                URI uri;
                try {
                    uri = new URI(gameParams.get("namingUri"));
                } catch (URISyntaxException e) {
                    throw new RuntimeException(e);
                }
                return new ServerlessHttpGame(uri);
            }
        }
        return new SingleServer(host, port);
    }
}

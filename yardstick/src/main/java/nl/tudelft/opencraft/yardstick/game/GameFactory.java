package nl.tudelft.opencraft.yardstick.game;

import java.util.Map;
import java.util.Objects;

public class GameFactory {
    public GameArchitecture getGame(String host, int port, Map<String, String> gameParams) {
        if (gameParams.containsKey("architecture")) {
            String archi = gameParams.get("architecture");
            if (archi.equals("serverless")) {
                String functionName = gameParams.get("functionName");
                String region = gameParams.get("region");
                Objects.requireNonNull(functionName);
                Objects.requireNonNull(region);
                return new ServerlessGame(functionName, region);
            }
        }
        return new SingleServer(host, port);
    }
}

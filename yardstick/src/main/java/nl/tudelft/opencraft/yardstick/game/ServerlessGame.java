package nl.tudelft.opencraft.yardstick.game;

import java.net.InetSocketAddress;
import java.text.MessageFormat;
import java.util.Random;
import software.amazon.awssdk.core.SdkBytes;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.lambda.LambdaClient;
import software.amazon.awssdk.services.lambda.model.InvokeRequest;
import software.amazon.awssdk.services.lambda.model.InvokeResponse;

/**
 * Represents a serverless Minecraft-like game, which does not have a central server.
 * Before a player can connect, they must ask the game's naming system where to connect to.
 */
public class ServerlessGame implements GameArchitecture {

    private final LambdaClient lambdaClient;
    private final Random random = new Random(0);

    private final String functionName;
    private final Region region;

    public ServerlessGame(String functionName, String region) {
        this.functionName = functionName;
        this.region = Region.of(region);
        this.lambdaClient = LambdaClient.builder().region(this.region).build();
    }

    /**
     * Obtains a unique address for one new player to connect to using the Minecraft protocol.
     *
     * @return a new address for a new player
     */
    @Override
    public InetSocketAddress getAddressForPlayer() {
        String id = String.valueOf(random.nextInt());
        String json = MessageFormat.format("'{' \"name\": \"servo/player:ID={0}\" '}'", id);
        SdkBytes payload = SdkBytes.fromUtf8String(json);
        InvokeResponse response = lambdaClient.invoke(InvokeRequest.builder()
                .functionName(functionName)
                .payload(payload)
                .build());
        String responseText = response.payload().asUtf8String().replaceAll("\"", "");
        String hostname = responseText.split(":")[0];
        int port = Integer.parseInt(responseText.split(":")[1]);
        return new InetSocketAddress(hostname, port);
    }
}

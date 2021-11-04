package nl.tudelft.opencraft.yardstick.game;

import java.net.InetSocketAddress;
import java.text.MessageFormat;
import java.time.Duration;
import java.util.Random;
import java.util.concurrent.CompletableFuture;
import software.amazon.awssdk.core.SdkBytes;
import software.amazon.awssdk.http.nio.netty.NettyNioAsyncHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.lambda.LambdaAsyncClient;
import software.amazon.awssdk.services.lambda.model.InvokeRequest;
import software.amazon.awssdk.services.lambda.model.InvokeResponse;

/**
 * Represents a serverless Minecraft-like game, which does not have a central server.
 * Before a player can connect, they must ask the game's naming system where to connect to.
 */
public class ServerlessAwsSdkGame implements GameArchitecture {

    private final LambdaAsyncClient lambdaClient;
    private final Random random = new Random(System.currentTimeMillis());

    private final String functionName;
    private final Region region;

    public ServerlessAwsSdkGame(String functionName, String region) {
        this.functionName = functionName;
        this.region = Region.of(region);
        Duration timeout = Duration.ofMinutes(15);
        this.lambdaClient = LambdaAsyncClient.builder()
                // These extended timeouts are needed to prevent the SDK from retrying a lambda that hasn't failed but
                // simply takes a long time.
                .httpClientBuilder(NettyNioAsyncHttpClient.builder()
                        .connectionMaxIdleTime(timeout)
                        .connectionTimeout(timeout)
                        .readTimeout(timeout)
                        .tcpKeepAlive(true))
                .region(Region.EU_CENTRAL_1)
                .build();
    }

    /**
     * Obtains a unique address for one new player to connect to using the Minecraft protocol.
     *
     * @return a new address for a new player
     */
    @Override
    public CompletableFuture<InetSocketAddress> getAddressForPlayer() {
        String id = String.valueOf(random.nextInt());
        String json = MessageFormat.format("'{' \"name\": \"servo/player:ID={0}\", \"action\": \"get\" '}'", id);
        SdkBytes payload = SdkBytes.fromUtf8String(json);
        var futureResponse = lambdaClient.invoke(InvokeRequest.builder()
                .functionName(functionName)
                .payload(payload)
                .build());
        InvokeResponse response = futureResponse.join();
        if (response.statusCode() != 200) {
            System.out.println(response.logResult());
        }
        String responseText = response.payload().asUtf8String().replaceAll("\"", "");
        System.out.println(responseText);
        int port = 25571;
        return CompletableFuture.completedFuture(new InetSocketAddress(responseText, port));
    }
}

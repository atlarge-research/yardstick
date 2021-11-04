package nl.tudelft.opencraft.yardstick.game;

import java.net.InetSocketAddress;
import java.util.concurrent.CompletableFuture;

public interface GameArchitecture {
    CompletableFuture<InetSocketAddress> getAddressForPlayer();
}

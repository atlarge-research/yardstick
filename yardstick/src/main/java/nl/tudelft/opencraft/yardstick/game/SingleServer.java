package nl.tudelft.opencraft.yardstick.game;

import java.net.InetSocketAddress;
import java.util.concurrent.CompletableFuture;

public class SingleServer implements GameArchitecture {

    private final InetSocketAddress addr;

    public SingleServer(String hostname, int port) {
        this.addr = new InetSocketAddress(hostname, port);
    }

    public SingleServer(InetSocketAddress addr) {
        this.addr = addr;
    }

    @Override
    public CompletableFuture<InetSocketAddress> getAddressForPlayer() {
        return CompletableFuture.completedFuture(addr);
    }
}

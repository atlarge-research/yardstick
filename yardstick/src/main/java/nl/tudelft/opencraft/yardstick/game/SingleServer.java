package nl.tudelft.opencraft.yardstick.game;

import java.net.InetSocketAddress;

public class SingleServer implements GameArchitecture {

    private final InetSocketAddress addr;

    public SingleServer(InetSocketAddress addr) {
        this.addr = addr;
    }

    @Override
    public InetSocketAddress getAddressForPlayer() {
        return addr;
    }
}

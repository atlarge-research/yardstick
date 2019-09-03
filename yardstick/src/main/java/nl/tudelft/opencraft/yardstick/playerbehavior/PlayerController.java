package nl.tudelft.opencraft.yardstick.playerbehavior;

import java.util.ArrayList;
import java.util.Collection;

public class PlayerController implements Runnable {

    private ArrayList<EmulatedPlayer> players = new ArrayList<>();
    private final PlayerBehavior playerBehavior;
    private final World world;

    public PlayerController(final Collection<EmulatedPlayer> players, final PlayerBehavior playerBehavior, final World world) {
        this.players.addAll(players);
        this.playerBehavior = playerBehavior;
        this.world = world;
    }

    @Override
    public void run() {
        for (EmulatedPlayer player : this.players) {
            this.playerBehavior.before(player, world);
        }
    }
}

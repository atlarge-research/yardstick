package nl.tudelft.opencraft.yardstick.playerbehavior;

public interface PlayerBehavior {
    void before(EmulatedPlayer player, World world);
    void tick(EmulatedPlayer player, World world);
    void done(EmulatedPlayer player, World world);
}

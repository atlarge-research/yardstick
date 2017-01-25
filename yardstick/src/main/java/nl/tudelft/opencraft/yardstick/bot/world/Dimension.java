package nl.tudelft.opencraft.yardstick.bot.world;

public enum Dimension {

    NETHER(-1),
    OVERWORLD(0),
    END(1);

    private final int id;

    private Dimension(int id) {
        this.id = id;
    }

    public int getId() {
        return id;
    }

    public static Dimension forId(int id) {
        for (Dimension d : Dimension.values()) {
            if (d.getId() == id) {
                return d;
            }
        }
        throw new IllegalArgumentException("Invalid dimension: " + id);
    }

}

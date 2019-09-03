package nl.tudelft.opencraft.yardstick.playerbehavior;

interface EmulatedPlayer {
    boolean isIdle();

    void sleep(int seconds);

    void disconnect(String reason);

    Task getTask();

    void setTask(Task activity);

    Vector3d getLocation();

    void log(String s);

    public String getName();

}
package nl.tudelft.opencraft.yardstick.bot;

import org.spacehq.mc.protocol.data.game.setting.Difficulty;

public class Server {

    private int maxPlayers;
    private Difficulty difficulty;

    public int getMaxPlayers() {
        return maxPlayers;
    }

    public Difficulty getDifficulty() {
        return difficulty;
    }

    public void setDifficulty(Difficulty difficulty) {
        this.difficulty = difficulty;
    }

    public void setMaxPlayers(int maxPlayers) {
        this.maxPlayers = maxPlayers;
    }

}

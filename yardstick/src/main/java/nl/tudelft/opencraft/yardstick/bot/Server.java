package nl.tudelft.opencraft.yardstick.bot;

import com.github.steveice10.mc.protocol.data.game.setting.Difficulty;

/**
 * Represents server-related data visible to the Bot.
 */
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

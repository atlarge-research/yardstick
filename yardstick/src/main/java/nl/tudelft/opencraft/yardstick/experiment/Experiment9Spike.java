/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2021 AtLarge Research
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

package nl.tudelft.opencraft.yardstick.experiment;

import com.typesafe.config.Config;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;

import java.time.Duration;

public class Experiment9Spike extends Experiment4MultiWalkAround {

    private final Config behaviorConfig;
    private Duration spikeDelay;
    private Duration spikeDuration;
    private int spikePeakPlayers;

    public Experiment9Spike(int nodeID, GameArchitecture game, Config config) {
        super(9, nodeID, game, config, "Operates bots according to experiment 4, but allows a temporary spike in " +
                "players after set delay.");
        this.behaviorConfig = config;
    }

    @Override
    protected void before() {
        super.before();
        spikeDelay = behaviorConfig.getDuration("spikeDelayInSeconds");
        spikeDuration = behaviorConfig.getDuration("spikeDurationInSeconds");
        spikePeakPlayers = behaviorConfig.getInt("spikePeakPlayers");
    }

    @Override
    protected void tick() {
        super.tick();
        boolean spikeHasStarted = System.currentTimeMillis() - getStartMillis() >= spikeDelay.toMillis();
        boolean spikeHasEnded =
                System.currentTimeMillis() - getStartMillis() >= spikeDelay.plus(spikeDuration).toMillis();
        if (spikeHasStarted && !spikeHasEnded) {
            boolean reachedPlayerPeak = currentNumberOfBots() >= spikePeakPlayers;
            boolean joinIntervalElapsed = System.currentTimeMillis() > getLastJoined() + joinIntervalInSeconds() * 1000;
            int numBotsToJoin = Math.min(getBotsPerJoin(), spikePeakPlayers - currentNumberOfBots());
            if (!reachedPlayerPeak && joinIntervalElapsed) {
                for (int i = 0; i < numBotsToJoin; i++) {
                    connectNewBot();
                }
            }
        } else if (spikeHasEnded && currentNumberOfBots() > getBotsTotal()) {
            disconnectBots(currentNumberOfBots() - getBotsTotal(), "player spike ended");
        }
    }
}

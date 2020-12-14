/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2020 AtLarge Research
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

package nl.tudelft.opencraft.yardstick.bot.entity;

import java.nio.charset.Charset;
import java.util.UUID;

import com.fasterxml.jackson.annotation.JsonIgnore;
import science.atlarge.opencraft.mcprotocollib.data.game.entity.player.GameMode;
import science.atlarge.opencraft.packetlib.Session;
import nl.tudelft.opencraft.yardstick.bot.Bot;

/**
 * Represents the bot as a player in the world.
 */
public class BotPlayer extends Player {

    @JsonIgnore
    private final Bot bot;
    @JsonIgnore
    private final Session session;
    //
    private GameMode gamemode;
    private boolean canFly;
    private double flySpeed;
    private double walkSpeed;
    private boolean invincible;
    private boolean flying;
    private double saturation;

    public BotPlayer(Bot bot, int id) {
        super(UUID.nameUUIDFromBytes(bot.getName().getBytes(Charset.forName("UTF-8"))), id);

        this.bot = bot;
        this.session = bot.getClient().getSession();
    }

    public Bot getBot() {
        return bot;
    }

    // TODO: Player actions, data
    public GameMode getGamemode() {
        return gamemode;
    }

    public void setGamemode(GameMode gamemode) {
        this.gamemode = gamemode;
    }

    public boolean getCanFly() {
        return canFly;
    }

    public void setCanFly(boolean canFly) {
        this.canFly = canFly;
    }

    public double getFlySpeed() {
        return flySpeed;
    }

    public void setFlySpeed(double flySpeed) {
        this.flySpeed = flySpeed;
    }

    public double getWalkSpeed() {
        return walkSpeed;
    }

    public void setWalkSpeed(double walkSpeed) {
        this.walkSpeed = walkSpeed;
    }

    public void setFlying(boolean flying) {
        this.flying = flying;
    }

    public boolean isFlying() {
        return flying;
    }

    public boolean isInvincible() {
        return invincible;
    }

    public void setInvincible(boolean invurnable) {
        this.invincible = invurnable;
    }

    public double getSaturation() {
        return saturation;
    }

    public void setSaturation(double saturation) {
        this.saturation = saturation;
    }

}

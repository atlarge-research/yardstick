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

package nl.tudelft.opencraft.yardstick.bot;

import com.github.steveice10.mc.protocol.MinecraftProtocol;
import com.github.steveice10.mc.protocol.data.SubProtocol;
import com.github.steveice10.mc.protocol.data.game.chunk.Column;
import com.github.steveice10.mc.protocol.data.game.entity.metadata.Position;
import com.github.steveice10.mc.protocol.data.game.entity.type.GlobalEntityType;
import com.github.steveice10.mc.protocol.data.game.world.block.BlockChangeRecord;
import com.github.steveice10.mc.protocol.packet.ingame.client.world.ClientTeleportConfirmPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerBossBarPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerChatPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerCombatPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerDifficultyPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerDisconnectPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerJoinGamePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerKeepAlivePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerPlayerListDataPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerPlayerListEntryPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerPluginMessagePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerResourcePackSendPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerRespawnPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerSetCooldownPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerStatisticsPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerSwitchCameraPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerTabCompletePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerTitlePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityAnimationPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityAttachPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityCollectItemPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityDestroyPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityEffectPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityEquipmentPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityHeadLookPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityMetadataPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityMovementPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityPositionPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityPositionRotationPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityPropertiesPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityRemoveEffectPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityRotationPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntitySetPassengersPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityStatusPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityTeleportPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityVelocityPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerVehicleMovePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.player.ServerPlayerAbilitiesPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.player.ServerPlayerChangeHeldItemPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.player.ServerPlayerHealthPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.player.ServerPlayerPositionRotationPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.player.ServerPlayerSetExperiencePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.player.ServerPlayerUseBedPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.spawn.ServerSpawnExpOrbPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.spawn.ServerSpawnGlobalEntityPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.spawn.ServerSpawnMobPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.spawn.ServerSpawnObjectPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.spawn.ServerSpawnPaintingPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.spawn.ServerSpawnPlayerPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.scoreboard.ServerDisplayScoreboardPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.scoreboard.ServerScoreboardObjectivePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.scoreboard.ServerTeamPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.scoreboard.ServerUpdateScorePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.window.ServerCloseWindowPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.window.ServerConfirmTransactionPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.window.ServerOpenWindowPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.window.ServerSetSlotPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.window.ServerWindowItemsPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.window.ServerWindowPropertyPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerBlockBreakAnimPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerBlockChangePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerBlockValuePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerChunkDataPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerExplosionPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerMapDataPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerMultiBlockChangePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerNotifyClientPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerOpenTileEntityEditorPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerPlayBuiltinSoundPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerPlayEffectPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerPlaySoundPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerSpawnParticlePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerSpawnPositionPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerUnloadChunkPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerUpdateTileEntityPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerUpdateTimePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.world.ServerWorldBorderPacket;
import com.github.steveice10.packetlib.Session;
import com.github.steveice10.packetlib.event.session.ConnectedEvent;
import com.github.steveice10.packetlib.event.session.DisconnectedEvent;
import com.github.steveice10.packetlib.event.session.DisconnectingEvent;
import com.github.steveice10.packetlib.event.session.PacketReceivedEvent;
import com.github.steveice10.packetlib.event.session.PacketSendingEvent;
import com.github.steveice10.packetlib.event.session.PacketSentEvent;
import com.github.steveice10.packetlib.event.session.SessionListener;
import com.github.steveice10.packetlib.packet.Packet;
import java.util.UUID;
import java.util.logging.Level;
import java.util.logging.Logger;
import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.entity.Entity;
import nl.tudelft.opencraft.yardstick.bot.entity.ExperienceOrb;
import nl.tudelft.opencraft.yardstick.bot.entity.LightningStrike;
import nl.tudelft.opencraft.yardstick.bot.entity.Mob;
import nl.tudelft.opencraft.yardstick.bot.entity.ObjectEntity;
import nl.tudelft.opencraft.yardstick.bot.entity.Painting;
import nl.tudelft.opencraft.yardstick.bot.entity.Player;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.Chunk;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkLocation;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.Dimension;
import nl.tudelft.opencraft.yardstick.bot.world.World;
import nl.tudelft.opencraft.yardstick.util.Vector3d;

/**
 * Handles basic bot network traffic.
 */
public class BotListener implements SessionListener {

    private final Bot bot;
    private final Logger logger;
    //
    private BotPlayer player;
    private Server server;
    private World world;

    /**
     * Creates a new listener.
     *
     * @param bot the bot to listen to.
     */
    public BotListener(Bot bot) {
        this.bot = bot;
        this.logger = bot.getLogger();
    }

    @Override
    public void packetReceived(PacketReceivedEvent pre) {
        MinecraftProtocol pro = (MinecraftProtocol) pre.getSession().getPacketProtocol();

        if (pro.getSubProtocol() != SubProtocol.GAME) {
            //logger.info("Received non-game packet: " + pre.getPacket().getClass().getName());
            return;
        }

        Packet packet = pre.getPacket();
        if (packet instanceof ServerSpawnObjectPacket) {
            // 0x00 Spawn Object
            ServerSpawnObjectPacket p = (ServerSpawnObjectPacket) packet;
            // TODO

            if (p.getEntityId() == 0) {
                logger.warning("Received spawn object with EID == 0: " + p.getType());
                return;
            }

            ObjectEntity obj = new ObjectEntity(p.getEntityId(), p.getUUID());
            obj.setLocation(new Vector3d(p.getX(), p.getY(), p.getZ()));
            obj.setPitch(p.getPitch());
            obj.setYaw(p.getYaw());
            obj.setVelocity(new Vector3d(p.getMotionX(), p.getMotionY(), p.getMotionZ()));
            obj.setData(0); // TODO: Figure out how to get the raw data
            obj.setType(p.getType());

            world.loadEntity(obj);

        } else if (packet instanceof ServerSpawnExpOrbPacket) {
            // 0x01 Spawn Experience Orb
            ServerSpawnExpOrbPacket p = (ServerSpawnExpOrbPacket) packet;

            // TODO: Aaah! XP orbs have no UUID! :O
            ExperienceOrb orb = new ExperienceOrb(p.getEntityId(), UUID.randomUUID());
            orb.setLocation(new Vector3d(p.getX(), p.getY(), p.getZ()));
            orb.setCount(p.getExp());
            world.loadEntity(orb);

        } else if (packet instanceof ServerSpawnGlobalEntityPacket) {
            // 0x02 Spawn Global Entity
            ServerSpawnGlobalEntityPacket p = (ServerSpawnGlobalEntityPacket) packet;

            if (p.getType() != GlobalEntityType.LIGHTNING_BOLT) {
                logger.warning("Received spawn global entity for non-lightning strike");
                return;
            }

            // TODO: Aaah! Lightning strikes have no UUID! :O
            LightningStrike ls = new LightningStrike(p.getEntityId(), UUID.randomUUID());
            ls.setLocation(new Vector3d(p.getX(), p.getY(), p.getZ()));
            world.loadEntity(ls);

            // TODO: Remove entity?
        } else if (packet instanceof ServerSpawnMobPacket) {
            // 0x03 Spawn Mob
            ServerSpawnMobPacket p = (ServerSpawnMobPacket) packet;

            // TODO: double check the getType().ordinal() works as expected.
            Entity e = new Mob(p.getEntityId(), p.getUUID(), p.getType());
            e.setLocation(new Vector3d(p.getX(), p.getY(), p.getZ()));
            e.setYaw(p.getYaw());
            e.setHeadYaw(p.getHeadYaw());
            e.setPitch(p.getPitch());
            e.setVelocity(new Vector3d(p.getMotionX(), p.getMotionY(), p.getMotionZ()));
            world.loadEntity(e);

        } else if (packet instanceof ServerSpawnPaintingPacket) {
            // 0x04 Spawn painting
            ServerSpawnPaintingPacket p = (ServerSpawnPaintingPacket) packet;

            Painting painting = new Painting(p.getEntityId(), p.getUUID());
            painting.setLocation(new Vector3d(p.getPosition().getX(), p.getPosition().getY(), p.getPosition().getZ()));
            // TODO: Direction, type
            world.loadEntity(painting);

        } else if (packet instanceof ServerSpawnPlayerPacket) {
            // 0x05 Spawn Player
            ServerSpawnPlayerPacket p = (ServerSpawnPlayerPacket) packet;

            Player pl = new Player(p.getUUID(), p.getEntityId());
            pl.setLocation(new Vector3d(p.getX(), p.getY(), p.getZ()));
            pl.setPitch(p.getPitch());
            pl.setYaw(p.getYaw());
            // TODO Metadata

            bot.getWorld().loadEntity(pl);

        } else if (packet instanceof ServerEntityAnimationPacket) {
            // 0x06 Animation
            ServerEntityAnimationPacket p = (ServerEntityAnimationPacket) packet;
            // TODO

        } else if (packet instanceof ServerStatisticsPacket) {
            // 0x07 Statistics
            ServerStatisticsPacket p = (ServerStatisticsPacket) packet;
            // TODO

        } else if (packet instanceof ServerBlockBreakAnimPacket) {
            // 0x08 Block Break Animation
            ServerBlockBreakAnimPacket p = (ServerBlockBreakAnimPacket) packet;
            // TODO

        } else if (packet instanceof ServerUpdateTileEntityPacket) {
            // 0x09 Update Block Entity
            ServerUpdateTileEntityPacket p = (ServerUpdateTileEntityPacket) packet;
            // TODO

        } else if (packet instanceof ServerBlockValuePacket) {
            // 0x0A Block Action
            ServerBlockValuePacket p = (ServerBlockValuePacket) packet;
            // TODO

        } else if (packet instanceof ServerBlockChangePacket) {
            // 0x0B Block Change
            ServerBlockChangePacket p = (ServerBlockChangePacket) packet;

            BlockChangeRecord r = p.getRecord();
            Position pos = r.getPosition();

            if (pos.getY() > 255) {
                // https://github.com/Steveice10/MCProtocolLib/issues/347
                logger.warning("Ignoring BlockChange: (" + pos.getX() + "," + pos.getY() + "," + pos.getZ() + ")");
                return;
            }

            Block b = null;
            try {
                b = bot.getWorld().getBlockAt(pos.getX(), pos.getY(), pos.getZ());
            } catch (ChunkNotLoadedException e) {
                logger.fine("Received BlockChange for block in unloaded chunk: " + pos);
                return;
            }

            b.setInternalState(r.getBlock());

        } else if (packet instanceof ServerBossBarPacket) {
            // 0x0C Boss Bar
            ServerBossBarPacket p = (ServerBossBarPacket) packet;
            // TODO

        } else if (packet instanceof ServerDifficultyPacket) {
            // 0x0D Server Difficulty
            ServerDifficultyPacket p = (ServerDifficultyPacket) packet;

            bot.getServer().setDifficulty(p.getDifficulty());

        } else if (packet instanceof ServerTabCompletePacket) {
            // 0x0E Tab-Complete
            ServerTabCompletePacket p = (ServerTabCompletePacket) packet;
            // TODO

        } else if (packet instanceof ServerChatPacket) {
            // 0x0F Chat Message
            ServerChatPacket p = (ServerChatPacket) packet;
            // TODO

        } else if (packet instanceof ServerMultiBlockChangePacket) {
            // 0x10 Multi Block Change
            ServerMultiBlockChangePacket p = (ServerMultiBlockChangePacket) packet;

            for (BlockChangeRecord r : p.getRecords()) {
                Position pos = r.getPosition();

                //logger.info("MultiBlockChange: (" + pos.getX() + "," + pos.getY() + "," + pos.getZ() + ")");
                Block b = null;
                try {
                    b = bot.getWorld().getBlockAt(pos.getX(), pos.getY(), pos.getZ());
                } catch (ChunkNotLoadedException e) {
                    logger.fine("Received MultiBlockChange for block in unloaded chunk: " + pos);
                    return;
                }

                b.setInternalState(r.getBlock());
            }

        } else if (packet instanceof ServerConfirmTransactionPacket) {
            // 0x11 Confirm Transaction
            ServerConfirmTransactionPacket p = (ServerConfirmTransactionPacket) packet;
            // TODO

        } else if (packet instanceof ServerCloseWindowPacket) {
            // 0x12 Close Window
            ServerCloseWindowPacket p = (ServerCloseWindowPacket) packet;
            // TODO

        } else if (packet instanceof ServerOpenWindowPacket) {
            // 0x13 Open Window
            ServerOpenWindowPacket p = (ServerOpenWindowPacket) packet;
            // TODO

        } else if (packet instanceof ServerWindowItemsPacket) {
            // 0x14 Window Items
            ServerWindowItemsPacket p = (ServerWindowItemsPacket) packet;
            // TODO

        } else if (packet instanceof ServerWindowPropertyPacket) {
            // 0x15 Window Property
            ServerWindowPropertyPacket p = (ServerWindowPropertyPacket) packet;
            // TODO

        } else if (packet instanceof ServerSetSlotPacket) {
            // 0x16 Set Slot
            ServerSetSlotPacket p = (ServerSetSlotPacket) packet;
            // TODO

        } else if (packet instanceof ServerSetCooldownPacket) {
            // 0x17 Set Cooldown
            ServerSetCooldownPacket p = (ServerSetCooldownPacket) packet;
            // TODO

        } else if (packet instanceof ServerPluginMessagePacket) {
            // 0x18 Plugin Message
            ServerPluginMessagePacket p = (ServerPluginMessagePacket) packet;
            // TODO

        } else if (packet instanceof ServerPlaySoundPacket) {
            // 0x19 Named Sound Effect
            ServerPlaySoundPacket p = (ServerPlaySoundPacket) packet;
            // TODO

        } else if (packet instanceof ServerDisconnectPacket) {
            // 0x1A Disconnect
            // Do nothing, handled by default listener.

        } else if (packet instanceof ServerEntityStatusPacket) {
            // 0x1B Entity Status
            ServerEntityStatusPacket p = (ServerEntityStatusPacket) packet;
            // TODO

        } else if (packet instanceof ServerExplosionPacket) {
            // 0x1C Explosion
            ServerExplosionPacket p = (ServerExplosionPacket) packet;
            // TODO - help the server exploded

        } else if (packet instanceof ServerUnloadChunkPacket) {
            // 0x1D Unload Chunk
            ServerUnloadChunkPacket p = (ServerUnloadChunkPacket) packet;

            world.unloadChunk(p.getX(), p.getZ());

        } else if (packet instanceof ServerNotifyClientPacket) {
            // 0x1E Change Game State
            ServerNotifyClientPacket p = (ServerNotifyClientPacket) packet;
            // TODO

        } else if (packet instanceof ServerKeepAlivePacket) {
            // 0x1F Keep Alive
            // Do nothing, handled by default listener.

        } else if (packet instanceof ServerChunkDataPacket) {
            // 0x20 Chunk Data
            ServerChunkDataPacket p = (ServerChunkDataPacket) packet;

            Column newCol = p.getColumn();
            try {
                Chunk chunk = world.getChunk(new ChunkLocation(newCol.getX(), newCol.getZ()));

                // col.hasBiomeData() is currently the only way to determine the 'ground-up contrinous' property.
                // See http://wiki.vg/Chunk_Format#Ground-up_continuous for more details
                if (newCol.hasBiomeData()) {
                    // Replace the previous chunk
                    //logger.info("Replacing pre-existing chunk: " + new ChunkLocation(newCol.getX(), newCol.getZ()));
                    world.loadChunk(new Chunk(world, p.getColumn()));
                } else {
                    // Only update the new chunk sections
                    String s = "";
                    for (int i = 0; i < newCol.getChunks().length; i++) {
                        if (newCol.getChunks()[i] == null) {
                            // Chunk not updated
                            continue;
                        }

                        s += "" + i + " ";

                        chunk.getHandle().getChunks()[i] = newCol.getChunks()[i];
                    }
                    //logger.info("Updating pre-existing chunk: " + new ChunkLocation(newCol.getX(), newCol.getZ()) + ", sections: " + s);
                }
            } catch (ChunkNotLoadedException ex) {
                // New chunk
                world.loadChunk(new Chunk(world, p.getColumn()));
            }

        } else if (packet instanceof ServerPlayEffectPacket) {
            // 0x21 Effect
            ServerPlayEffectPacket p = (ServerPlayEffectPacket) packet;
            // TODO

        } else if (packet instanceof ServerSpawnParticlePacket) {
            // 0x22 Particle
            ServerSpawnParticlePacket p = (ServerSpawnParticlePacket) packet;
            // TODO

        } else if (packet instanceof ServerJoinGamePacket) {
            // 0x23 Join Game
            ServerJoinGamePacket p = (ServerJoinGamePacket) packet;
            // TODO: Reduced debug info field?

            // Init the game
            this.world = new World(Dimension.forId(p.getDimension()), p.getWorldType());
            bot.setWorld(world);

            this.server = new Server();
            server.setMaxPlayers(p.getMaxPlayers());
            server.setDifficulty(p.getDifficulty());
            bot.setServer(server);

            this.player = new BotPlayer(bot, p.getEntityId());
            player.setGamemode(p.getGameMode());
            bot.setPlayer(player);
        } else if (packet instanceof ServerMapDataPacket) {
            // 0x24 Map
            ServerMapDataPacket p = (ServerMapDataPacket) packet;
            // TODO

        } else if (packet instanceof ServerEntityMovementPacket) {
            // 0x25 Entity Relative Move
            // 0x26 Entity Look And Relative Move
            // 0x27 Entity Look
            // 0x28 Entity

            ServerEntityMovementPacket p = (ServerEntityMovementPacket) packet;

            Entity e = world.getEntity(p.getEntityId());
            if (e == null) {
                return;
            }

            if (packet instanceof ServerEntityPositionPacket) {
                // 0x25
                e.setLocation(e.getLocation().add(new Vector3d(p.getMovementX(), p.getMovementY(), p.getMovementZ())));
                e.setOnGround(p.isOnGround());
            } else if (packet instanceof ServerEntityRotationPacket) {
                // 0x27
                e.setPitch(p.getPitch());
                e.setYaw(p.getYaw());
                e.setOnGround(p.isOnGround());
            } else if (packet instanceof ServerEntityPositionRotationPacket) {
                // 0x26
                e.setLocation(e.getLocation().add(new Vector3d(p.getMovementX(), p.getMovementY(), p.getMovementZ())));
                e.setPitch(p.getPitch());
                e.setYaw(p.getYaw());
                e.setOnGround(p.isOnGround());
            } else {
                // 0x28
                // Do nothing.
            }

        } else if (packet instanceof ServerVehicleMovePacket) {
            // 0x29 Vehicle Move
            ServerVehicleMovePacket p = (ServerVehicleMovePacket) packet;
            // TODO

        } else if (packet instanceof ServerOpenTileEntityEditorPacket) {
            // 0x2A Open Sign Editor
            ServerOpenTileEntityEditorPacket p = (ServerOpenTileEntityEditorPacket) packet;
            // TODO

        } else if (packet instanceof ServerPlayerAbilitiesPacket) {

            // 0x2B Player Abilities
            ServerPlayerAbilitiesPacket p = (ServerPlayerAbilitiesPacket) packet;

            BotPlayer player = bot.getPlayer();
            if (player != null) {
                player.setFlySpeed(p.getFlySpeed());
                player.setWalkSpeed(p.getWalkSpeed());
                player.setInvincible(p.getInvincible());
                player.setFlying(p.getFlying());
                player.setCanFly(p.getCanFly());
            }
            // TODO: Creative mode?

        } else if (packet instanceof ServerCombatPacket) {
            // 0x2C Combat Event
            ServerCombatPacket p = (ServerCombatPacket) packet;
            // TODO

        } else if (packet instanceof ServerPlayerListEntryPacket) {
            // 0x2D Player List Item
            ServerPlayerListEntryPacket p = (ServerPlayerListEntryPacket) packet;
            // TODO

        } else if (packet instanceof ServerPlayerPositionRotationPacket) {
            // 0x2E Player Position And Look
            ServerPlayerPositionRotationPacket p = (ServerPlayerPositionRotationPacket) packet;

            BotPlayer player = bot.getPlayer();
            player.setLocation(new Vector3d(p.getX(), p.getY(), p.getZ()));
            player.setPitch(p.getPitch());
            player.setYaw(p.getYaw());
            player.setOnGround(true);

            Session session = bot.getClient().getSession();
            session.send(new ClientTeleportConfirmPacket(p.getTeleportId()));

            logger.info("Received new Player position: " + player.getLocation());

        } else if (packet instanceof ServerPlayerUseBedPacket) {
            // 0x2F Use Bed
            ServerPlayerUseBedPacket p = (ServerPlayerUseBedPacket) packet;
            // TODO

        } else if (packet instanceof ServerEntityDestroyPacket) {
            // 0x30 Destroy Entities
            ServerEntityDestroyPacket p = (ServerEntityDestroyPacket) packet;

            for (int id : p.getEntityIds()) {
                if (world.isEntityLoaded(id)) {
                    world.unloadEntity(id);
                }
            }
        } else if (packet instanceof ServerEntityRemoveEffectPacket) {
            // 0x31 Remove Entity Effect
            ServerEntityRemoveEffectPacket p = (ServerEntityRemoveEffectPacket) packet;
            // TODO

        } else if (packet instanceof ServerResourcePackSendPacket) {
            // 0x32 Resource Pack Send
            ServerResourcePackSendPacket p = (ServerResourcePackSendPacket) packet;
            // TODO

        } else if (packet instanceof ServerRespawnPacket) {
            // 0x33 Respawn
            ServerRespawnPacket p = (ServerRespawnPacket) packet;
            // TODO

        } else if (packet instanceof ServerEntityHeadLookPacket) {
            // 0x34 Entity Head Look
            ServerEntityHeadLookPacket p = (ServerEntityHeadLookPacket) packet;

            Entity e = world.getEntity(p.getEntityId());
            if (e == null) {
                return;
            }

            e.setHeadYaw(p.getHeadYaw());

        } else if (packet instanceof ServerWorldBorderPacket) {
            // 0x35 World Border
            ServerWorldBorderPacket p = (ServerWorldBorderPacket) packet;
            // TODO

        } else if (packet instanceof ServerSwitchCameraPacket) {
            // 0x36 Camera
            ServerSwitchCameraPacket p = (ServerSwitchCameraPacket) packet;
            // TODO

        } else if (packet instanceof ServerPlayerChangeHeldItemPacket) {
            // 0x37 Held Item Change
            ServerPlayerChangeHeldItemPacket p = (ServerPlayerChangeHeldItemPacket) packet;
            // TODO

        } else if (packet instanceof ServerDisplayScoreboardPacket) {
            // 0x38 Display Scoreboard
            ServerDisplayScoreboardPacket p = (ServerDisplayScoreboardPacket) packet;
            // TODO

        } else if (packet instanceof ServerEntityMetadataPacket) {
            // 0x39 Entity Metadata
            ServerEntityMetadataPacket p = (ServerEntityMetadataPacket) packet;
            // TODO

        } else if (packet instanceof ServerEntityAttachPacket) {
            // 0x3A Attach Entity
            ServerEntityAttachPacket p = (ServerEntityAttachPacket) packet;
            // TODO

        } else if (packet instanceof ServerEntityVelocityPacket) {
            // 0x3B Entity Velocity
            ServerEntityVelocityPacket p = (ServerEntityVelocityPacket) packet;

            Entity e = world.getEntity(p.getEntityId());
            if (e == null) {
                return;
            }
            e.setVelocity(new Vector3d(p.getMotionX(), p.getMotionY(), p.getMotionZ()));

        } else if (packet instanceof ServerEntityEquipmentPacket) {
            // 0x3C Entity Equipment
            ServerEntityEquipmentPacket p = (ServerEntityEquipmentPacket) packet;
            // TODO

        } else if (packet instanceof ServerPlayerSetExperiencePacket) {
            // 0x3D Set Experience
            ServerPlayerSetExperiencePacket p = (ServerPlayerSetExperiencePacket) packet;
            // TODO

        } else if (packet instanceof ServerPlayerHealthPacket) {
            // 0x3E Update Health
            ServerPlayerHealthPacket p = (ServerPlayerHealthPacket) packet;

            player.setHealth(p.getHealth());

        } else if (packet instanceof ServerScoreboardObjectivePacket) {
            // 0x3F Scoreboard objective
            ServerScoreboardObjectivePacket p = (ServerScoreboardObjectivePacket) packet;
            // TODO

        } else if (packet instanceof ServerEntitySetPassengersPacket) {
            // 0x40 Set Passengers
            ServerEntitySetPassengersPacket p = (ServerEntitySetPassengersPacket) packet;
            // TODO

        } else if (packet instanceof ServerTeamPacket) {
            // 0x41 Teams
            ServerTeamPacket p = (ServerTeamPacket) packet;
            // TODO

        } else if (packet instanceof ServerUpdateScorePacket) {
            // 0x42 Update Score
            ServerUpdateScorePacket p = (ServerUpdateScorePacket) packet;
            // TODO

        } else if (packet instanceof ServerSpawnPositionPacket) {
            // 0x43 Spawn Position
            ServerSpawnPositionPacket p = (ServerSpawnPositionPacket) packet;

            world.setSpawnPoint(p.getPosition());

        } else if (packet instanceof ServerUpdateTimePacket) {
            // 0x44 Time Update
            ServerUpdateTimePacket p = (ServerUpdateTimePacket) packet;
            // TODO

        } else if (packet instanceof ServerTitlePacket) {
            // 0x45 Title
            ServerTitlePacket p = (ServerTitlePacket) packet;
            // TODO

        } else if (packet instanceof ServerPlayBuiltinSoundPacket) {
            // 0x46 Sound Effect
            ServerPlayBuiltinSoundPacket p = (ServerPlayBuiltinSoundPacket) packet;
            // TODO

        } else if (packet instanceof ServerPlayerListDataPacket) {
            // 0x47 Player List Header And Footer
            ServerPlayerListDataPacket p = (ServerPlayerListDataPacket) packet;
            // TODO

        } else if (packet instanceof ServerEntityCollectItemPacket) {
            // 0x48 Collect Item
            ServerEntityCollectItemPacket p = (ServerEntityCollectItemPacket) packet;
            // TODO

        } else if (packet instanceof ServerEntityTeleportPacket) {
            // 0x49 Entity Teleport
            ServerEntityTeleportPacket p = (ServerEntityTeleportPacket) packet;

            Entity e = world.getEntity(p.getEntityId());
            if (e == null) {
                return;
            }

            e.setLocation(new Vector3d(p.getX(), p.getY(), p.getZ()));
            e.setYaw(p.getYaw());
            e.setPitch(p.getPitch());

        } else if (packet instanceof ServerEntityPropertiesPacket) {
            // 0x4A Entity Properties
            ServerEntityPropertiesPacket p = (ServerEntityPropertiesPacket) packet;
            // TODO

        } else if (packet instanceof ServerEntityEffectPacket) {
            // 0x4B Entity Effect
            ServerEntityEffectPacket p = (ServerEntityEffectPacket) packet;
            // TODO

        } else {
            logger.warning("Received unhandled packet: " + packet.getClass().getName());
        }
    }

    @Override
    public void packetSending(PacketSendingEvent packetSendingEvent) {

    }

    @Override
    public void packetSent(PacketSentEvent pse) {
    }

    @Override
    public void connected(ConnectedEvent ce) {
    }

    @Override
    public void disconnecting(DisconnectingEvent de) {
    }

    @Override
    public void disconnected(DisconnectedEvent de) {
        logger.info("Disconnected: " + de.getReason());
        if (de.getCause() != null) {
            logger.log(Level.WARNING, "Connection closed unexpectedly!", de.getCause());
        }
    }

}

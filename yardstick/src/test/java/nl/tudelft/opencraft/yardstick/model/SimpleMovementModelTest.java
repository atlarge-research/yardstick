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

package nl.tudelft.opencraft.yardstick.model;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.bot.world.World;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import com.github.steveice10.mc.protocol.data.game.entity.metadata.Position;

@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class SimpleMovementModelTest {

    @Mock
    Bot mockBot;
    @Mock
    BotPlayer mockPlayer;
    @Mock
    World mockWorld;
    @Mock
    Block traversableBlock;
    @Mock
    Block nonTraversableBlock;

    @BeforeAll
    public void setup() {
        MockitoAnnotations.initMocks(this);
    }

    @BeforeEach
    public void init() throws ChunkNotLoadedException {
        Mockito.when(mockBot.getPlayer()).thenReturn(mockPlayer);
        Mockito.when(mockBot.getWorld()).thenReturn(mockWorld);
        Mockito.when(traversableBlock.getRelative(Mockito.any(BlockFace.class))).thenReturn(nonTraversableBlock);
    }

    @Test
    void testNewFieldLocation() throws ChunkNotLoadedException {
        Mockito.when(mockPlayer.getLocation()).thenReturn(Vector3d.ZERO);
        Mockito.when(mockWorld.getBlockAt(Mockito.anyInt(), Mockito.anyInt(), Mockito.anyInt())).thenReturn(traversableBlock);
        Mockito.when(traversableBlock.getMaterial()).thenReturn(Material.AIR);
        Mockito.when(nonTraversableBlock.getMaterial()).thenReturn(Material.DIRT);

        SimpleMovementModel model = new SimpleMovementModel();

        for (int i = 0; i < 1000; i++) {
            Vector3i location = model.getNewFieldLocation(mockBot);

            Assertions.assertTrue(location.getX() <= 32, "Value was " + location.getX());
            Assertions.assertTrue(location.getZ() <= 32, "Value was " + location.getZ());
            Assertions.assertTrue(location.getX() >= -32, "Value was " + location.getX());
            Assertions.assertTrue(location.getZ() >= -32, "Value was " + location.getZ());
        }
    }

    @Test
    void testNewFieldLocationAnchor() throws ChunkNotLoadedException {
        Mockito.when(mockPlayer.getLocation()).thenReturn(new Vector3d(100, 100, 100));
        Mockito.when(mockWorld.getBlockAt(Mockito.anyInt(), Mockito.anyInt(), Mockito.anyInt())).thenReturn(traversableBlock);
        Mockito.when(mockWorld.getSpawnPoint()).thenReturn(new Position(0, 0, 0));
        Mockito.when(traversableBlock.getMaterial()).thenReturn(Material.AIR);
        Mockito.when(nonTraversableBlock.getMaterial()).thenReturn(Material.DIRT);

        SimpleMovementModel model = new SimpleMovementModel(32, true);

        for (int i = 0; i < 1000; i++) {
            Vector3i location = model.getNewFieldLocation(mockBot);

            Assertions.assertTrue(location.getX() <= 32, "Value was " + location.getX());
            Assertions.assertTrue(location.getZ() <= 32, "Value was " + location.getZ());
            Assertions.assertTrue(location.getX() >= -32, "Value was " + location.getX());
            Assertions.assertTrue(location.getZ() >= -32, "Value was " + location.getZ());
        }
    }
}

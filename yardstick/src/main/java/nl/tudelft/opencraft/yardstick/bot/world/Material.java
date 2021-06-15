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
 *
 * Copyright (c) 2013, DarkStorm (darkstorm@evilminecraft.net)
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
package nl.tudelft.opencraft.yardstick.bot.world;

import nl.tudelft.opencraft.yardstick.bot.inventory.ToolType;
import static nl.tudelft.opencraft.yardstick.bot.inventory.ToolType.*;
import static nl.tudelft.opencraft.yardstick.bot.world.Material.Flag.*;
import java.util.Arrays;

public enum Material {

    UNKNOWN(-1),
    AIR(0, TRAVERSABLE),
    STONE(1, PICKAXE),
    GRASS(2, SHOVEL),
    DIRT(3, SHOVEL),
    COBBLESTONE(4, PICKAXE),
    WOOD(5, AXE),
    SAPLING(6, TRAVERSABLE | INTERACTABLE),
    BEDROCK(7, INDESTRUCTABLE),
    WATER(8, TRAVERSABLE | FLUID | INDESTRUCTABLE),
    STATIONARY_WATER(9, TRAVERSABLE | FLUID | INDESTRUCTABLE),
    LAVA(10, TRAVERSABLE | FLUID | INDESTRUCTABLE),
    STATIONARY_LAVA(11, TRAVERSABLE | FLUID | INDESTRUCTABLE),
    SAND(12, SHOVEL),
    GRAVEL(13, SHOVEL),
    GOLD_ORE(14, PICKAXE),
    IRON_ORE(15, PICKAXE),
    COAL_ORE(16, PICKAXE),
    LOG(17, AXE),
    LEAVES(18, SHEARS),
    SPONGE(19),
    GLASS(20, PICKAXE),
    LAPIS_ORE(21, PICKAXE),
    LAPIS_BLOCK(22, PICKAXE),
    DISPENSER(23, INTERACTABLE, PICKAXE),
    SANDSTONE(24, PICKAXE),
    NOTE_BLOCK(25, INTERACTABLE, PICKAXE),
    BED_BLOCK(26, INTERACTABLE),
    POWERED_RAIL(27, PICKAXE),
    DETECTOR_RAIL(28, PICKAXE),
    PISTON_STICKY_BASE(29, PICKAXE),
    WEB(30, TRAVERSABLE, SWORD),
    LONG_GRASS(31, TRAVERSABLE),
    DEAD_BUSH(32, TRAVERSABLE),
    PISTON_BASE(33, PICKAXE),
    PISTON_EXTENSION(34, PICKAXE),
    WOOL(35, SWORD),
    PISTON_MOVING_PIECE(36),
    YELLOW_FLOWER(37, TRAVERSABLE),
    RED_FLOWER(38, TRAVERSABLE),
    BROWN_MUSHROOM(39, TRAVERSABLE),
    RED_MUSHROOM(40, TRAVERSABLE),
    GOLD_BLOCK(41, PICKAXE),
    IRON_BLOCK(42, PICKAXE),
    DOUBLE_STEP(43, PICKAXE),
    STEP(44, PICKAXE),
    BRICK(45, PICKAXE),
    TNT(46),
    BOOKSHELF(47, AXE),
    MOSSY_COBBLESTONE(48, PICKAXE),
    OBSIDIAN(49, PICKAXE),
    TORCH(50, TRAVERSABLE),
    FIRE(51, INDESTRUCTABLE),
    MOB_SPAWNER(52, PICKAXE),
    WOOD_STAIRS(53, AXE),
    CHEST(54, INTERACTABLE, AXE),
    REDSTONE_WIRE(55),
    DIAMOND_ORE(56, PICKAXE),
    DIAMOND_BLOCK(57, PICKAXE),
    WORKBENCH(58, INTERACTABLE, AXE),
    //CROPS(59),
    SOIL(60, SHOVEL),
    FURNACE(61, INTERACTABLE, PICKAXE),
    BURNING_FURNACE(62, INTERACTABLE, PICKAXE),
    SIGN_POST(63, TRAVERSABLE, 16, AXE),
    WOODEN_DOOR(64, TRAVERSABLE, INTERACTABLE, AXE),
    LADDER(65, TRAVERSABLE),
    RAILS(66, TRAVERSABLE, PICKAXE),
    COBBLESTONE_STAIRS(67, PICKAXE),
    WALL_SIGN(68, TRAVERSABLE, AXE),
    LEVER(69, TRAVERSABLE, INTERACTABLE),
    STONE_PLATE(70, TRAVERSABLE, PICKAXE),
    IRON_DOOR_BLOCK(71, TRAVERSABLE, PICKAXE),
    WOOD_PLATE(72, TRAVERSABLE, AXE),
    REDSTONE_ORE(73, TRAVERSABLE, PICKAXE),
    GLOWING_REDSTONE_ORE(74, TRAVERSABLE, PICKAXE),
    REDSTONE_TORCH_OFF(75, TRAVERSABLE),
    REDSTONE_TORCH_ON(76, TRAVERSABLE),
    STONE_BUTTON(77, TRAVERSABLE, INTERACTABLE, PICKAXE),
    SNOW(78, TRAVERSABLE, SHOVEL),
    ICE(79, PICKAXE),
    SNOW_BLOCK(80, SHOVEL),
    CACTUS(81),
    CLAY(82, SHOVEL),
    SUGAR_CANE_BLOCK(83),
    JUKEBOX(84, PICKAXE),
    FENCE(85, AXE),
    PUMPKIN(86, AXE),
    NETHERRACK(87, PICKAXE),
    SOUL_SAND(88, SHOVEL),
    GLOWSTONE(89, PICKAXE),
    PORTAL(90 | INDESTRUCTABLE),
    JACK_O_LANTERN(91, AXE),
    CAKE_BLOCK(92),
    DIODE_BLOCK_OFF(93, INTERACTABLE),
    DIODE_BLOCK_ON(94, INTERACTABLE),
    LOCKED_CHEST(95, AXE),
    TRAP_DOOR(96, TRAVERSABLE | INTERACTABLE, AXE),
    MONSTER_EGGS(97),
    SMOOTH_BRICK(98, PICKAXE),
    HUGE_MUSHROOM_1(99, AXE),
    HUGE_MUSHROOM_2(100, AXE),
    IRON_FENCE(101, PICKAXE),
    THIN_GLASS(102, PICKAXE),
    MELON_BLOCK(103, AXE),
    PUMPKIN_STEM(104),
    MELON_STEM(105),
    VINE(106),
    FENCE_GATE(107, TRAVERSABLE | INTERACTABLE, AXE),
    BRICK_STAIRS(108, PICKAXE),
    SMOOTH_STAIRS(109, PICKAXE),
    MYCEL(110, SHOVEL),
    WATER_LILY(111),
    NETHER_BRICK(112, PICKAXE),
    NETHER_FENCE(113, PICKAXE),
    NETHER_BRICK_STAIRS(114, PICKAXE),
    NETHER_WARTS(115),
    ENCHANTMENT_TABLE(116, PICKAXE),
    BREWING_STAND(117, PICKAXE),
    CAULDRON(118, PICKAXE),
    ENDER_PORTAL(119, TRAVERSABLE, INDESTRUCTABLE),
    ENDER_PORTAL_FRAME(120, INDESTRUCTABLE),
    ENDER_STONE(121, PICKAXE),
    DRAGON_EGG(122 | INTERACTABLE),
    REDSTONE_LAMP_OFF(123, PICKAXE),
    REDSTONE_LAMP_ON(124, PICKAXE),
    WOOD_DOUBLE_STEP(125, AXE),
    WOOD_STEP(126, AXE),
    COCOA(127),
    SANDSTONE_STAIRS(128, PICKAXE),
    EMERALD_ORE(129, PICKAXE),
    ENDER_CHEST(130, INDESTRUCTABLE | INTERACTABLE),
    TRIPWIRE_HOOK(131, TRAVERSABLE),
    TRIPWIRE(132, TRAVERSABLE),
    EMERALD_BLOCK(133, PICKAXE),
    SPRUCE_WOOD_STAIRS(134, AXE),
    BIRCH_WOOD_STAIRS(135, AXE),
    JUNGLE_WOOD_STAIRS(136, AXE),
    COMMAND(137),
    BEACON(138, PICKAXE),
    COBBLE_WALL(139, PICKAXE),
    FLOWER_POT(140),
    CARROT(141),
    POTATO(142),
    WOOD_BUTTON(143, INTERACTABLE, AXE),
    SKULL(144),
    ANVIL(145, PICKAXE),
    TRAPPED_CHEST(146, PICKAXE),
    LIGHT_WEIGHTED_PRESSURE_PLATE(147, TRAVERSABLE, PICKAXE),
    HEAVY_WEIGHTED_PRESSURE_PLATE(148, TRAVERSABLE, PICKAXE),
    DAYLIGHT_SENSOR(151, PICKAXE),
    REDSTONE_BLOCK(152, PICKAXE),
    NETHER_QUARTZ_ORE(153, PICKAXE),
    HOPPER(154, PICKAXE),
    QUARTZ_BLOCK(155, PICKAXE),
    QUARTZ_STAIRS(156, PICKAXE),
    ACTIVATOR_RAIL(157, TRAVERSABLE, PICKAXE),
    DROPPER(158, PICKAXE),
    STAINED_CLAY(159, PICKAXE),
    STAINED_GLASS_PANE(160, PICKAXE),
    LEAVES2(161, SHEARS),
    LOG2(162, AXE),
    ACACIA_STAIRS(163, AXE),
    DARK_OAK_STAIRS(164, AXE),
    SLIME_BLOCK(165),
    BARRIER(166, INDESTRUCTABLE),
    IRON_TRAPDOOR(167, PICKAXE),
    PRISMARINE(168, PICKAXE),
    SEA_LANTERN(169),
    HAY_BALE(170),
    CARPET(171, TRAVERSABLE),
    HARDENED_CLAY(172, PICKAXE),
    COAL_BLOCK(173, PICKAXE),
    PACKED_ICE(174, PICKAXE),
    DOUBLE_PLANT(175, TRAVERSABLE),
    RED_SANDSTONE(179, PICKAXE),
    RED_SANDSTONE_STAIRS(180, PICKAXE),
    RED_SANDSTONE_SLAB(182, PICKAXE),
    SPRUCE_FENCE_GATE(183, TRAVERSABLE),
    BIRCH_FENCE_GATE(184, TRAVERSABLE),
    JUNGLE_FENCE_GATE(185, TRAVERSABLE),
    DARK_OAK_FENCE_GATE(186, TRAVERSABLE),
    ACADIA_FENCE_GATE(187, TRAVERSABLE),
    SPRUCE_FENCE(183, AXE),
    BIRCH_FENCE(184, AXE),
    JUNGLE_FENCE(185, AXE),
    DARK_OAK_FENCE(186, AXE),
    ACADIA_FENCE(187, AXE);
    //
    private final int id, maxStack, flags;
    private final ToolType toolType;

    private static final Integer[] traversable_states = {0, 21, 23, 25, 27, 29, 31, 1341,
            62, 63, 64, -124, -123, -122, -121, -120, -119, -118, -117, -38,
            -116, -115, -114, -113, -112, -111, -110, 108, -73, -65, -64,
            -64, -62, -61, -60, -59, -58, -57, -56, -54, -53, -52, -51, -50,
            62, 114, -112, 78, 101, 3887, -88, 61, 44, 32, -78, 1342, 7897};

    private static final Integer[] fluid_states = {34, 35, 36, 37, 38, 39, 41, 42,  50, 52, 54, 56, 11, -84};

    private Material(int id) {
        this(id, ToolType.PICKAXE);
    }

    private Material(int id, ToolType toolType) {
        this(id, 64, toolType);
    }

    private Material(int id, int flags) {
        this(id, flags, 64);
    }

    private Material(int id, int flags, ToolType toolType) {
        this(id, flags, 64, toolType);
    }

    private Material(int id, int flags, int maxStack) {
        this(id, flags, maxStack, null);
    }

    private Material(int id, int flags, int maxStack, ToolType toolType) {
        this.id = id;
        this.flags = flags;
        this.maxStack = maxStack;
        this.toolType = toolType;
    }

    public int getId() {
        return id;
    }

    public int getMaxStack() {
        return maxStack;
    }

    public boolean isTraversable() {
        return (flags & TRAVERSABLE) == TRAVERSABLE;
    }

    public static boolean isStateTraversable(int state) {
        return Arrays.asList(traversable_states).contains(state);
    }
    public static boolean isStateFluid(int state) {
        return Arrays.asList(fluid_states).contains(state);
    }

    public boolean isInteractable() {
        return (flags & INTERACTABLE) == INTERACTABLE;
    }

    public boolean isIndestructable() {
        return (flags & INDESTRUCTABLE) == INDESTRUCTABLE;
    }

    public boolean isFluid() {
        return (flags & FLUID) == FLUID;
    }

    public ToolType getToolType() {
        return toolType;
    }

    public static Material getById(int id) {
        for (Material type : values()) {
            if (type.getId() == id) {
                return type;
            }
        }
        return UNKNOWN;
    }

    /**
     * Represents flags for a world.
     */
    protected static final class Flag {

        /**
         * Indicates a player is able to traverse this block. This implies the
         * FLUID flag. Blocks that are not traversable can be stood on, and are
         * called 'solid'.
         */
        public static final int TRAVERSABLE = 1;
        /**
         * Indicates a player can interact with this block.
         */
        public static final int INTERACTABLE = 2;
        /**
         * Indicates a player cannot destroy this block.
         */
        public static final int INDESTRUCTABLE = 4;
        /**
         * Indicates this block is a fluid.
         */
        public static final int FLUID = 8;
    }

}

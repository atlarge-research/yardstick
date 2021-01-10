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

package nl.tudelft.opencraft.yardstick.bot.inventory;

public enum ToolType {
    SWORD(268, 272, 267, 283, 276),
    PICKAXE(270, 274, 257, 285, 278),
    SHOVEL(269, 273, 256, 284, 277),
    AXE(271, 275, 258, 286, 279),
    HOE(290, 291, 292, 294, 293),
    SHEARS(359);

    private final int[] ids;

    private ToolType(int... ids) {
        this.ids = ids;
    }

    public int[] getIds() {
        return ids.clone();
    }

    public static ToolType getById(int id) {
        for (ToolType type : values()) {
            for (int typeId : type.ids) {
                if (id == typeId) {
                    return type;
                }
            }
        }
        return null;
    }
}

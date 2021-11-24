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

package nl.tudelft.opencraft.yardstick;

import com.beust.jcommander.Parameter;

/**
 * Represents command line options for the emulator.
 */
public class Options {

    @Parameter(names = {"--help"}, help = true, description = "Shows help")
    public boolean help;

    @Parameter(names = {"--address"}, description = "The hostname of the game.")
    public String address;

    @Parameter(names = {"--nodeID"}, description = "The ID of this node, in [0, #nodes-1]")
    public int nodeID;

    /**
     * CSV dumps
     */
    @Parameter(names = {"--csvdump", "-cd"}, description = "Convert a workload file to CSV format")
    public boolean csvDump;

    @Parameter(names = "--input", description = "An input file to read from. To be used with --csvdump")
    public String inFile;

    @Parameter(names = "--output", description = "An output file to write to. To be used with --csvdump")
    public String outFile;


    @Override
    public String toString() {
        final StringBuilder sb = new StringBuilder("Options{");
        sb.append("help=").append(help);
        sb.append(", address='").append(address).append('\'');
        sb.append(", csvDump=").append(csvDump);
        sb.append(", inFile='").append(inFile).append('\'');
        sb.append(", outFile='").append(outFile).append('\'');
        sb.append('}');
        return sb.toString();
    }
}

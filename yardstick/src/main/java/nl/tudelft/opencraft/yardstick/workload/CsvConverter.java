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

package nl.tudelft.opencraft.yardstick.workload;

import com.google.common.io.CountingInputStream;
import com.google.common.io.CountingOutputStream;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.EOFException;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.zip.GZIPInputStream;

/**
 * Utility class to convert binary capture files to CSV-formatted files.
 */
public class CsvConverter {

    private static final Logger logger = LoggerFactory.getLogger(CsvConverter.class);

    private CsvConverter() {
    }

    /**
     * Convert a binary message capture file to a CSV-formatted file. The input
     * file must exist, the output file may.
     *
     * @param inFileName  the input filename.
     * @param outFileName the output filename.
     */
    public static void convertCsv(String inFileName, String outFileName) {
        File inFile = new File(inFileName);
        File outFile = new File(outFileName);

        if (!inFile.exists() || !inFile.isFile()) {
            logger.error("File does not exist: {}", inFileName);
            return;
        }

        // In
        DataInputStream in;
        CountingInputStream inCos;
        try {
            FileInputStream fos = new FileInputStream(inFile);
            inCos = new CountingInputStream(fos);
            GZIPInputStream gos = new GZIPInputStream(inCos);
            BufferedInputStream bos2 = new BufferedInputStream(gos);
            in = new DataInputStream(bos2);
        } catch (IOException ex) {
            logger.error("Could not read from file: " + inFileName, ex);
            return;
        }

        // Out
        BufferedOutputStream out;
        CountingOutputStream outCos;
        try {
            outFile.getCanonicalFile().getParentFile().mkdirs();
            FileOutputStream fos = new FileOutputStream(outFile);
            outCos = new CountingOutputStream(fos);
            out = new BufferedOutputStream(outCos);
        } catch (IOException ex) {
            logger.error("Could not write to file: " + outFileName, ex);
            return;
        }

        logger.info("Converting: {}", inFileName);
        int packets = 0;
        try {
            writeString(out, "timestamp,outgoing,name,length\n");

            while (in.available() > 0) {

                // Handle GZIPInputStream not accurately returning in.available() == 0
                // when the end of the stream has been reached.
                in.mark(1);
                try {
                    in.readByte();
                    in.reset();
                } catch (EOFException ex) {
                    break;
                }

                // Read
                PacketEntry entry = PacketEntry.readFrom(in);

                // Write
                String csv = entry.toCsv();
                writeString(out, csv);
                packets++;
            }

            String compression = String.format("%.1f", ((double) outCos.getCount()) / inCos.getCount());
            logger.info("Converted {} packets. Compression ratio: {}", packets, compression);
        } catch (Exception ex) {
            logger.error("Could not convert to CSV: {}. At packet: {}", outFileName, packets, ex);
        } finally {
            try {
                in.close();
            } catch (IOException ex) {
            }
            try {
                out.close();
            } catch (IOException ex) {
            }
        }

    }

    private static void writeString(OutputStream out, String string) throws IOException {
        out.write(string.getBytes(StandardCharsets.UTF_8));
    }

}

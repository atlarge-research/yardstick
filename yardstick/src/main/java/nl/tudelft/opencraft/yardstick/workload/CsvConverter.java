package nl.tudelft.opencraft.yardstick.workload;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.EOFException;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.zip.GZIPInputStream;
import com.google.common.io.CountingInputStream;
import com.google.common.io.CountingOutputStream;
import nl.tudelft.opencraft.yardstick.Yardstick;

public class CsvConverter {

    private static final Logger LOGGER = Yardstick.LOGGER.newSubLogger("CSV Converter");

    private CsvConverter() {
    }

    public static void convertCsv(String inFileName, String outFileName) {
        File inFile = new File(inFileName);
        File outFile = new File(outFileName);

        if (!inFile.exists() || !inFile.isFile()) {
            LOGGER.severe("File does not exist: " + inFileName);
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
            LOGGER.log(Level.SEVERE, "Could not read from file: " + inFileName, ex);
            return;
        }

        // Out
        BufferedOutputStream out;
        CountingOutputStream outCos;
        outFile.getCanonicalFile().getParentFile().mkdirs();
        try {
            FileOutputStream fos = new FileOutputStream(outFile);
            outCos = new CountingOutputStream(fos);
            out = new BufferedOutputStream(outCos);
        } catch (FileNotFoundException ex) {
            LOGGER.log(Level.SEVERE, "Could not write to file: " + outFileName, ex);
            return;
        }

        LOGGER.info("Converting: " + inFileName);
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
            LOGGER.info("Converted " + packets + " packets. Compression ratio: " + compression);
        } catch (Exception ex) {
            LOGGER.log(Level.SEVERE, "Could not convert to CSV: " + outFileName + ". At packet: " + packets, ex);
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

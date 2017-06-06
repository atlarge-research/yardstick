package nl.tudelft.opencraft.yardstick.workload;

import com.github.steveice10.packetlib.packet.Packet;
import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.util.PacketUtil;

public class FilePacketDumper implements AutoCloseable {

    private static final SubLogger LOGGER = GlobalLogger.getLogger().newSubLogger("WorkLoadFileDumper");
    //
    private final File file;
    private final DataOutputStream dos;
    
    public FilePacketDumper(File file) throws IOException {
        this.file = file;

        FileOutputStream fos = new FileOutputStream(file);
        BufferedOutputStream bos = new BufferedOutputStream(fos);
        //GZIPOutputStream gos = new GZIPOutputStream(bos);
        this.dos = new DataOutputStream(bos);
    }
    
    public void dump(Packet packet, boolean outgoing) {
        try {
            long length = PacketUtil.packetLength(packet);
            
            // Write the data to the dump
            dos.writeLong(System.currentTimeMillis());
            dos.writeByte(outgoing ? 1 : 2);
            String packetName = packet.getClass().getSimpleName();
            
            byte[] bytes = packetName.getBytes(StandardCharsets.UTF_8);
            dos.writeInt(bytes.length);
            dos.write(bytes);
            dos.writeLong(length);
        } catch (IOException ex) {
            LOGGER.log(Level.SEVERE, "Could not write packet: " + packet.getClass().getSimpleName(), ex);
        }
    }

    @Override
    public void close() throws Exception {
        dos.flush();
        dos.close();
    }
    
    
    
}

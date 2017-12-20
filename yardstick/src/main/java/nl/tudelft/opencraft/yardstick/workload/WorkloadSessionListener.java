package nl.tudelft.opencraft.yardstick.workload;

import com.github.steveice10.packetlib.event.session.PacketReceivedEvent;
import com.github.steveice10.packetlib.event.session.PacketSentEvent;
import com.github.steveice10.packetlib.event.session.SessionAdapter;

public class WorkloadSessionListener extends SessionAdapter {

    private final WorkloadDumper dumper;
    private final String botName;

    public WorkloadSessionListener(WorkloadDumper dumper, String botName) {
        this.dumper = dumper;
        this.botName = botName;
    }

    @Override
    public void packetReceived(PacketReceivedEvent pre) {
        dumper.packetReceived(botName, pre);
    }

    @Override
    public void packetSent(PacketSentEvent pse) {
        dumper.packetSent(botName, pse);
    }

}

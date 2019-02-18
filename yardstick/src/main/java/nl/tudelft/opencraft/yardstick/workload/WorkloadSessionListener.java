package nl.tudelft.opencraft.yardstick.workload;

import com.github.steveice10.packetlib.event.session.PacketReceivedEvent;
import com.github.steveice10.packetlib.event.session.PacketSentEvent;
import com.github.steveice10.packetlib.event.session.SessionAdapter;

/**
 * A {@link SessionAdapter} which writes packets to a {@link WorkloadDumper}.
 */
public class WorkloadSessionListener extends SessionAdapter {

    private final WorkloadDumper dumper;
    private final String botName;

    /**
     * Creates a new WorkloadSessionListener.
     *
     * @param dumper the dumper to use.
     * @param botName The name of the bot this listener is attached to.
     */
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

package nl.tudelft.opencraft.yardstick.experiment;

import com.github.steveice10.mc.auth.data.GameProfile;
import com.github.steveice10.mc.auth.exception.request.RequestException;
import com.github.steveice10.mc.protocol.MinecraftConstants;
import com.github.steveice10.mc.protocol.data.game.ClientRequest;
import com.github.steveice10.mc.protocol.data.game.PlayerListEntry;
import com.github.steveice10.mc.protocol.data.game.entity.player.GameMode;
import com.github.steveice10.mc.protocol.data.game.entity.player.Hand;
import com.github.steveice10.mc.protocol.data.game.entity.player.PlayerAction;
import com.github.steveice10.mc.protocol.data.message.TextMessage;
import com.github.steveice10.mc.protocol.data.status.ServerStatusInfo;
import com.github.steveice10.mc.protocol.data.status.handler.ServerInfoHandler;
import com.github.steveice10.mc.protocol.packet.ingame.client.ClientChatPacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.ClientKeepAlivePacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.ClientRequestPacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerActionPacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerMovementPacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerStatePacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerSwingArmPacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.world.ClientSpectatePacket;
import com.github.steveice10.mc.protocol.packet.status.client.StatusQueryPacket;
import com.github.steveice10.packetlib.Client;
import com.github.steveice10.packetlib.Session;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import com.github.steveice10.packetlib.packet.Packet;
import nl.tudelft.opencraft.yardstick.bot.world.BlockMaterial;


import java.util.*;

public class Experiment8 extends Experiment {

    public static final long EXPERIMENT_DURATION = 10000;
    //
    private Client client;
    private Bot bot;
    private boolean done = false;
    public int tickCounter = 1;
    public static final Scanner cmdScanner = new Scanner(System.in);
    //
    private final List<Bot> botList = Collections.synchronizedList(new ArrayList<>());

    private int botsTotal = 0;
    private int currentBots = 0;
    private int listUpdateSeconds;
    private long lastUpdate = System.currentTimeMillis();

    private int afkUpdateSeconds = 30;
    private long afkUpdate = System.currentTimeMillis();

    public Experiment8() {
        super(8,
                "Bot that teleports to players and logs the incoming packets of surrounding players. ");
    }

    @Override
    protected void before() {
        this.botsTotal = Integer.parseInt(options.experimentParams.getOrDefault("bots","2"));
        this.listUpdateSeconds = Integer.parseInt(options.experimentParams.getOrDefault("updateInterval","600"));;
    }

    @Override
    protected void tick() {
        while (botList.size()<botsTotal) {
            synchronized (botList) {
                try {
                    int no = (botList.size()+1);
                    this.bot = newBot(options.experimentParams.getOrDefault("account" + no, "YSBot-" + no),options.experimentParams.getOrDefault("pw" + no, ""));
                    botList.add(bot);
                } catch (RequestException e) {
                    logger.severe("Could not connect bot. Stopping experiment.");
                    e.printStackTrace();
                    this.done = true;
                    return;
                }
            }
        }
        synchronized (botList){
            for (Bot bot: botList){
                if(!bot.isConnected()) {
                    bot.connect();
                    logger.info("Connected: " + bot.getName());
                }
            }
        }
        if (System.currentTimeMillis() - this.lastUpdate > listUpdateSeconds * 1000){
            //Timed teleport
            synchronized (botList){
                for (Bot bot : botList){
                    bot.setTeleport();
                }
            }
            this.lastUpdate = System.currentTimeMillis();

        }
        if (System.currentTimeMillis() - this.afkUpdate > afkUpdateSeconds * 1000){
            //Swing arm to prevent afk flag
            synchronized (botList){
                for (Bot bot : botList){
                    bot.getClient().getSession().send(new ClientPlayerSwingArmPacket(Hand.MAIN_HAND));
                }
            }
            this.afkUpdate = System.currentTimeMillis();

        }
        synchronized (botList) {
            for (Bot bot : botList) {
                botTick(bot);
            }
        }
    }



    private void botTick(Bot bot) {
        if(bot.getTeleport()) {
            //Teleport to a random player and try to enable specator mode if it is allowed to.
            checkGamemode(bot);
            teleportToRandom(bot);
        }
        checkDeath(bot);
    }

    private void checkGamemode(Bot bot){
        try {
            if(!bot.getPlayer().getGamemode().equals(GameMode.SPECTATOR)){
                bot.getClient().getSession().send(new ClientChatPacket("/gamemode spectator"));
            }
        } catch (NullPointerException n){

        }
    }

    private void checkDeath(Bot bot){
        try {
            if (bot.getPlayer().getHealth() == 0) {
                logger.warning("Bot died, attempting respawn");
                bot.getClient().getSession().send(new ClientRequestPacket(ClientRequest.RESPAWN));
            }
        } catch (NullPointerException e){

        }
    }

    private void teleportToRandom(Bot bot){
        // TODO figure out frequency? Check for other bot names
        int randomNo = 0;
        Random randomizer = new Random();
        String tpTarget = bot.getName();
        /* Debug print player list before teleporting
        String m = "";
        for (PlayerListEntry pl : bot.getPlayers()){
            if(pl != null){m = m + ", " + pl.getProfile().getName();}
        }
        logger.info(bot.getName() + " list : " + m);
         */
        while (tpTarget != null && tpTarget.equals(bot.getName())){
            randomNo = randomizer.nextInt(bot.getPlayers().length);
            if (bot.getPlayers()[randomNo] != null) {
                tpTarget = bot.getPlayers()[randomNo].getProfile().getName();
            }
        }
        bot.setFollowing(bot.getPlayers()[randomNo].getProfile().getId(),tpTarget);
        bot.getClient().getSession().send(new ClientChatPacket("/tp " + tpTarget));
        //bot.getClient().getSession().send(new ClientChatPacket("/tp " + bot.getPlayer().getLocation().getX() + " 100 " + bot.getPlayer().getLocation().getZ()));
        bot.setTeleport();
    }

    @Override
    protected void after() {
        client.getSession().disconnect("disconnect");
    }

    @Override
    public boolean isDone() {
        return done;// || !client.getSession().isConnected();
    }

}
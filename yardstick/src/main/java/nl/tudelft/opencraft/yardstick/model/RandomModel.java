package nl.tudelft.opencraft.yardstick.model;

import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.StandExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.experiment.Experiment12RandomE2E;

import java.util.ArrayList;
import java.util.Random;
import java.util.UUID;


public class RandomModel implements BotModel {
    private BotModel interact = new SimpleInteractionModel();
    private BotModel movement = new SimpleMovementModel();

    private String GMuser;
    private long GMInterval;
    private ArrayList<String> bannedUser = new ArrayList<>();

    public RandomModel(){

    }

    @Override
    public TaskExecutor newTask(Bot bot)  {
        TaskExecutor taskExecutor = null;
        Random RANDOM = new Random(System.nanoTime());
        double random = RANDOM.nextDouble();

        // GM execute command
        if (bot.getName().equals(GMuser)) {
            if (System.currentTimeMillis() - Experiment12RandomE2E.GMStartTime >= GMInterval * 1000) {
                String command = null;

                switch (Experiment12RandomE2E.GMCommand) {
                    case "weather":
                        if (random < 1/2.0)
                            command = "/weather clear";
                        else command = "/weather thunder";
                        break;

                    case "random": default:
                        if (random < 1 / 2.0) {
                            if (RANDOM.nextDouble() < 1 / 2.0) {
                                String target = UUID.randomUUID().toString().substring(0, 6);
                                command = "/ban " + target;
                                bannedUser.add(target);
                            } else if (bannedUser.size() > 0) {
                                int index = RANDOM.nextInt(bannedUser.size());
                                command = "/pardon " + bannedUser.get(index);
                                bannedUser.remove(index);
                            }
                        } else {
                            command = "/banlist";
                        }
                        break;
                }

                if (command != null) {
                    Experiment12RandomE2E.GMStartTime = System.currentTimeMillis();
                    bot.getController().sendChatMsg(command);
                }
            }
        }


        if (random <= 0.3) {
            // Interact
            taskExecutor = interact.newTask(bot);
        }
        else if (random > 0.3 && random <= 0.7) {
            // Movement
            taskExecutor = movement.newTask(bot);

            // random walk speed between [0.1, 0.4]
            double walkSpeed = RANDOM.nextDouble() * 0.4;
            if (walkSpeed < 0.1)
                walkSpeed = 0.15;
            ((WalkTaskExecutor) taskExecutor).setSpeed(walkSpeed);
        }

        else if (random > 0.7 && random <= 0.8) {
            // send msg
            if (RANDOM.nextDouble() < 0.5)
                bot.getController().sendChatMsg("hey");
            // get item
            else {
                Material mt = Material.getById(RANDOM.nextInt(187));
                if (mt != Material.UNKNOWN)
                    bot.getController().creativeInventoryAction(mt, RANDOM.nextInt(9) + 1);
            }
            StandExecutor stand = new StandExecutor(bot);
            stand.setTimeout(500);
            return stand;
        }

        // stand still
        else {
            return new StandExecutor(bot);
        }

        return taskExecutor;
    }

    public void setMovementDiameter(int dia) {
        movement = new SimpleMovementModel(dia);
    }

    public void setGMUser(String GMuser) {
        this.GMuser = GMuser;
    }

    public void setGMInterval(long GMInterval) {
        this.GMInterval = GMInterval;
    }
}

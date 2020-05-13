package nl.tudelft.opencraft.yardstick.bot.entity;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStream;
import java.util.List;
import java.util.Objects;
import java.util.Scanner;
import java.util.UUID;

import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;
import nl.tudelft.opencraft.yardstick.bot.world.BlockMaterial;
import nl.tudelft.opencraft.yardstick.util.Vector3d;

import com.github.steveice10.mc.protocol.data.game.entity.metadata.EntityMetadata;
import com.github.steveice10.mc.protocol.data.game.entity.attribute.Attribute;

/**
 * Represents an entity.
 *
 * <p>
 * http://wiki.vg/Entities#Entity</p>
 */
public class Entity {

    protected final int id;
    protected final UUID uuid;
    //
    protected Vector3d location;
    protected double yaw, headYaw, pitch;
    protected Vector3d velocity;
    protected boolean onGround = true;
    protected List<Attribute> attributes;
    protected EntityMetadata[] metadata;
    // TODO: Metadata

    public Entity(int id, UUID uuid) {
        this.id = id;
        this.uuid = uuid;
    }

    public int getId() {
        return id;
    }

    public UUID getUuid() {
        return uuid;
    }

    public Vector3d getLocation() {
        return location;
    }

    public double getYaw() {
        return yaw;
    }

    public double getHeadYaw() {
        return headYaw;
    }

    public double getPitch() {
        return pitch;
    }

    public Vector3d getVelocity() {
        return velocity;
    }

    public boolean isOnGround() {
        return onGround;
    }

    public void setLocation(Vector3d location) {
        this.location = location;
    }

    public void setYaw(double yaw) {
        this.yaw = yaw;
    }

    public void setHeadYaw(double headYaw) {
        this.headYaw = headYaw;
    }

    public void setPitch(double pitch) {
        this.pitch = pitch;
    }

    public void setVelocity(Vector3d velocity) {
        this.velocity = velocity;
    }

    public void setOnGround(boolean onGround) {
        this.onGround = onGround;
    }

    public void setAttributes(List<Attribute> attributes) { this.attributes = attributes; }
    public List<Attribute> getAttributes() { return attributes; }

    public EntityMetadata[] getMetadata() {return metadata;}
    public void setMetadata(EntityMetadata[] metadata) { this.metadata = metadata; }

    @Override
    public int hashCode() {
        int hash = 5;
        hash = 97 * hash + this.id;
        hash = 97 * hash + Objects.hashCode(this.uuid);
        return hash;
    }

    @Override
    public boolean equals(Object obj) {
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        final Entity other = (Entity) obj;
        if (this.id != other.id) {
            return false;
        }
        if (!Objects.equals(this.uuid, other.uuid)) {
            return false;
        }
        return true;
    }

    public static String getItem(int id){
        InputStream is = null;
        try {
            is = new FileInputStream("registries.json");
        } catch (FileNotFoundException e){
            System.out.println(("file not found"));
            return null;
        }
        String jsonString = new Scanner(is, "UTF-8").useDelimiter("\\Z").next();
        Configuration configuration = Configuration.builder().options(Option.AS_PATH_LIST).build();
        //Object dataObject = JsonPath.parse(jsonString).read("$..id");
        Object dataObject = JsonPath.using(configuration).parse(jsonString).read("$.['minecraft:item']..[?(@.protocol_id == "+id+")]");
        String dataString = dataObject.toString();
        String delims1 = "[\\[']+";
        String[] tokens = dataString.split(delims1);
        return tokens[6];
    }

    public static String getHeldItem(int id){
        InputStream is = null;
        try {
            is = new FileInputStream("registries.json");
        } catch (FileNotFoundException e){
            System.out.println(("file not found"));
            return null;
        }
        String jsonString = new Scanner(is, "UTF-8").useDelimiter("\\Z").next();
        Configuration configuration = Configuration.builder().options(Option.AS_PATH_LIST).build();
        //Object dataObject = JsonPath.parse(jsonString).read("$..id");
        Object dataObject = JsonPath.using(configuration).parse(jsonString).read("$.['minecraft:item']..[?(@.protocol_id == "+id+")]");
        String dataString = dataObject.toString();
        String delims1 = "[\\[']+";
        String[] tokens = dataString.split(delims1);
        return tokens[6];
    }
}

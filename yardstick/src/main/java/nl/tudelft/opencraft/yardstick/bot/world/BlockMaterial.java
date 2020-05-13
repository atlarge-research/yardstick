package nl.tudelft.opencraft.yardstick.bot.world;

import net.minidev.json.JSONArray;
import nl.tudelft.opencraft.yardstick.bot.inventory.ToolType;
import static nl.tudelft.opencraft.yardstick.bot.inventory.ToolType.*;
import static nl.tudelft.opencraft.yardstick.bot.world.Material.Flag.*;

import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.DocumentContext;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

public class BlockMaterial {

    public BlockMaterial(){
    }

    public static String getMaterial(int id){
        InputStream is = null;
        try {
            is = new FileInputStream("blocks.json");
        } catch (FileNotFoundException e){
            System.out.println(("file not found"));
            return null;
        }
        String jsonString = new Scanner(is, "UTF-8").useDelimiter("\\Z").next();
        Configuration configuration = Configuration.builder().options(Option.AS_PATH_LIST).build();
        //Object dataObject = JsonPath.parse(jsonString).read("$..id");
        Object dataObject = JsonPath.using(configuration).parse(jsonString).read("$..[?(@.id == "+id+")]");
        String dataString = dataObject.toString();
        String delims1 = "[\\[']+";
        String[] tokens = dataString.split(delims1);
        return tokens[2];
    }


}

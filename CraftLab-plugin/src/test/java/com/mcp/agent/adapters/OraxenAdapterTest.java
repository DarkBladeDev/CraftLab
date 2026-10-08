package com.mcp.agent.adapters;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mcp.agent.adapters.oraxen.OraxenItemExporter;
import org.bukkit.configuration.file.YamlConfiguration;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.*;

public class OraxenAdapterTest {

    @Test
    public void testOraxenItemExporter(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("OraxenAdapterTest");
        OraxenItemExporter exporter = new OraxenItemExporter(tempDir, logger);

        JsonObject item = new JsonObject();
        item.addProperty("id", "volcanic_blade");
        item.addProperty("material", "NETHERITE_SWORD");
        item.addProperty("display_name", "<red>Volcanic Blade</red>");
        item.addProperty("custom_model_data", 14001);

        JsonArray lore = new JsonArray();
        lore.add("<gray>Forged in nether core</gray>");
        item.add("lore", lore);

        JsonObject props = new JsonObject();
        JsonObject packProps = new JsonObject();
        packProps.addProperty("model", "custom/weapons/volcanic");
        props.add("Pack", packProps);
        item.add("plugin_properties", props);

        boolean success = exporter.exportItem(item);
        assertTrue(success);

        File exportedFile = new File(tempDir, "platform_items.yml");
        assertTrue(exportedFile.exists());

        YamlConfiguration yaml = YamlConfiguration.loadConfiguration(exportedFile);
        assertEquals("NETHERITE_SWORD", yaml.getString("volcanic_blade.material"));
        assertEquals("<red>Volcanic Blade</red>", yaml.getString("volcanic_blade.displayname"));
        assertEquals(14001, yaml.getInt("volcanic_blade.Pack.custom_model_data"));
        assertEquals("custom/weapons/volcanic", yaml.getString("volcanic_blade.Pack.model"));
        assertEquals(1, yaml.getStringList("volcanic_blade.lore").size());
    }
}

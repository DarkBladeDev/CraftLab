package com.mcp.agent.props;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.*;

public class PropStorageTest {

    @Test
    public void testPropStorageLifecycle(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("PropStorageTest");
        PropStorage storage = new PropStorage(tempDir, logger);

        // 1. Definition saving and loading
        PropDefinition chairDef = new PropDefinition("oak_chair", "Oak Chair", "studio:furniture/oak_chair");
        chairDef.setMode("display_prop");
        chairDef.setScale(Arrays.asList(1.2f, 1.2f, 1.2f));
        chairDef.setHitboxType("solid");
        chairDef.setHitboxOffsets(Arrays.asList(new int[]{0, 0, 0}));
        chairDef.setInteractionType("seat");
        chairDef.setSeatHeight(0.45f);
        chairDef.setDropItemId("oak_chair_item");

        chairDef.setBlockModel("studio:block/oak_chair_block");
        storage.saveDefinition(chairDef);

        PropDefinition retrievedDef = storage.getDefinition("oak_chair");
        assertNotNull(retrievedDef);
        assertEquals("Oak Chair", retrievedDef.getDisplayName());
        assertEquals("display_prop", retrievedDef.getMode());
        assertEquals("studio:block/oak_chair_block", retrievedDef.getBlockModel());
        assertEquals("studio:furniture/oak_chair", retrievedDef.getItemModel());
        assertEquals(0.45f, retrievedDef.getSeatHeight());
        assertEquals("seat", retrievedDef.getInteractionType());
        assertEquals(1.2f, retrievedDef.getScale().get(0));

        // 2. Placed instance saving and querying
        UUID instanceId = UUID.randomUUID();
        PropInstance instance = new PropInstance(
                instanceId,
                "oak_chair",
                "world",
                100, 64, 200,
                180.0f,
                System.currentTimeMillis()
        );
        storage.saveInstance(instance);

        assertEquals(1, storage.getAllInstances().size());
        PropInstance loadedInstance = storage.getInstanceAt("world", 100, 64, 200);
        assertNotNull(loadedInstance);
        assertEquals(instanceId, loadedInstance.getInstanceId());
        assertEquals("oak_chair", loadedInstance.getPropId());
        assertEquals(180.0f, loadedInstance.getYaw());

        // 3. Persistence across restart
        PropStorage reloaded = new PropStorage(tempDir, logger);
        assertNotNull(reloaded.getDefinition("oak_chair"));
        assertEquals("studio:block/oak_chair_block", reloaded.getDefinition("oak_chair").getBlockModel());
        assertNotNull(reloaded.getInstanceAt("world", 100, 64, 200));

        // 4. Removal
        reloaded.removeInstance(instanceId);
        assertNull(reloaded.getInstanceAt("world", 100, 64, 200));
        assertEquals(0, reloaded.getAllInstances().size());
    }

    @Test
    public void testSafeAlterTableMigration(@TempDir File tempDir) throws Exception {
        Logger logger = Logger.getLogger("PropStorageMigrationTest");
        File dbFile = new File(tempDir, "props.db");
        String url = "jdbc:sqlite:" + dbFile.getAbsolutePath();

        // Create legacy table without block_model
        try (java.sql.Connection conn = java.sql.DriverManager.getConnection(url);
             java.sql.Statement stmt = conn.createStatement()) {
            stmt.execute("CREATE TABLE prop_definitions (" +
                    "id TEXT PRIMARY KEY, " +
                    "display_name TEXT NOT NULL, " +
                    "mode TEXT NOT NULL, " +
                    "item_model TEXT, " +
                    "scale_json TEXT NOT NULL, " +
                    "translation_json TEXT NOT NULL, " +
                    "hitbox_type TEXT NOT NULL, " +
                    "hitbox_offsets_json TEXT NOT NULL, " +
                    "interaction_type TEXT, " +
                    "seat_height REAL NOT NULL, " +
                    "hardness REAL NOT NULL, " +
                    "tool_type TEXT NOT NULL, " +
                    "drop_item_id TEXT" +
                    ")");

            stmt.execute("INSERT INTO prop_definitions VALUES (" +
                    "'legacy_bench', 'Legacy Bench', 'display_prop', 'studio:legacy/bench', " +
                    "'[1.0, 1.0, 1.0]', '[0.0, 0.0, 0.0]', 'solid', '[[0,0,0]]', 'seat', 0.5, 1.0, 'AXE', NULL)");
        }

        // Initialize PropStorage over the legacy database
        PropStorage storage = new PropStorage(tempDir, logger);

        // Verify existing legacy definition loads safely with fallback block_model = item_model
        PropDefinition loaded = storage.getDefinition("legacy_bench");
        assertNotNull(loaded);
        assertEquals("legacy_bench", loaded.getId());
        assertEquals("studio:legacy/bench", loaded.getItemModel());
        assertEquals("studio:legacy/bench", loaded.getBlockModel());

        // Verify saving definition with block_model works on migrated table
        PropDefinition newDef = new PropDefinition("modern_lamp", "Modern Lamp", "studio:item/lamp", "studio:block/lamp");
        storage.saveDefinition(newDef);

        PropDefinition loadedNew = storage.getDefinition("modern_lamp");
        assertNotNull(loadedNew);
        assertEquals("studio:block/lamp", loadedNew.getBlockModel());
    }

    @Test
    public void testMultiStatePropLifecycle(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("PropStorageStateTest");
        PropStorage storage = new PropStorage(tempDir, logger);

        PropDefinition lampDef = new PropDefinition("lamp", "Vintage Lamp", "studio:item/lamp", "studio:props/lamp_off");
        lampDef.setDefaultState("off");

        java.util.Map<String, PropDefinition.PropState> states = new java.util.LinkedHashMap<>();
        PropDefinition.PropState offState = new PropDefinition.PropState();
        offState.setName("Apagada");
        offState.setBlockModel("studio:props/lamp_off");
        offState.setLightLevel(0);
        offState.setNextState("on");
        states.put("off", offState);

        PropDefinition.PropState onState = new PropDefinition.PropState();
        onState.setName("Encendida");
        onState.setBlockModel("studio:props/lamp_on");
        onState.setLightLevel(14);
        onState.setSound(new PropDefinition.PropStateSound("block.wooden_button.click_on", 0.8f, 1.0f));
        onState.setNextState("off");
        states.put("on", onState);

        lampDef.setStates(states);
        storage.saveDefinition(lampDef);

        PropDefinition retrievedDef = storage.getDefinition("lamp");
        assertNotNull(retrievedDef);
        assertEquals("off", retrievedDef.getDefaultState());
        assertEquals(2, retrievedDef.getStates().size());
        assertEquals("studio:props/lamp_on", retrievedDef.getBlockModelForState("on"));
        assertEquals("studio:props/lamp_off", retrievedDef.getBlockModelForState("off"));
        assertEquals(14, retrievedDef.getState("on").getLightLevel());
        assertNotNull(retrievedDef.getState("on").getSound());
        assertEquals("block.wooden_button.click_on", retrievedDef.getState("on").getSound().getKey());

        // Test instance state and state update in SQLite
        UUID instanceId = UUID.randomUUID();
        PropInstance instance = new PropInstance(
                instanceId,
                "lamp",
                "world",
                10, 64, 10,
                0.0f,
                System.currentTimeMillis(),
                "off"
        );
        storage.saveInstance(instance);

        PropInstance loadedInstance = storage.getInstanceAt("world", 10, 64, 10);
        assertNotNull(loadedInstance);
        assertEquals("off", loadedInstance.getCurrentState());

        // Update state to "on"
        storage.updateInstanceState(instanceId, "on");

        PropStorage reloadedStorage = new PropStorage(tempDir, logger);
        PropInstance reloadedInstance = reloadedStorage.getInstanceAt("world", 10, 64, 10);
        assertNotNull(reloadedInstance);
        assertEquals("on", reloadedInstance.getCurrentState());
    }

    @Test
    public void testPropDefinitionFromJsonWithStates() {
        com.google.gson.JsonObject json = new com.google.gson.JsonObject();
        json.addProperty("id", "test_door");
        json.addProperty("display_name", "Test Door");
        json.addProperty("default_state", "closed");

        com.google.gson.JsonObject statesObj = new com.google.gson.JsonObject();

        com.google.gson.JsonObject closedObj = new com.google.gson.JsonObject();
        closedObj.addProperty("block_model", "studio:props/door_closed");
        closedObj.addProperty("hitbox_type", "solid");
        closedObj.addProperty("next_state", "open");
        statesObj.add("closed", closedObj);

        com.google.gson.JsonObject openObj = new com.google.gson.JsonObject();
        openObj.addProperty("block_model", "studio:props/door_open");
        openObj.addProperty("hitbox_type", "passable");
        openObj.addProperty("next_state", "closed");
        statesObj.add("open", openObj);

        json.add("states", statesObj);

        PropDefinition def = PropDefinition.fromJson(json);
        assertEquals("test_door", def.getId());
        assertEquals("closed", def.getDefaultState());
        assertEquals("studio:props/door_closed", def.getBlockModelForState("closed"));
        assertEquals("studio:props/door_open", def.getBlockModelForState("open"));
        assertEquals("passable", def.getState("open").getHitboxType());
        assertEquals("solid", def.getState("closed").getHitboxType());
    }
}

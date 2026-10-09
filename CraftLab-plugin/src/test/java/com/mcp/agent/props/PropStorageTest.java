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
}

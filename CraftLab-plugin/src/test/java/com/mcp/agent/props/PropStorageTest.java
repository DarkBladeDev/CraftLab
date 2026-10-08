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

        storage.saveDefinition(chairDef);

        PropDefinition retrievedDef = storage.getDefinition("oak_chair");
        assertNotNull(retrievedDef);
        assertEquals("Oak Chair", retrievedDef.getDisplayName());
        assertEquals("display_prop", retrievedDef.getMode());
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
        assertNotNull(reloaded.getInstanceAt("world", 100, 64, 200));

        // 4. Removal
        reloaded.removeInstance(instanceId);
        assertNull(reloaded.getInstanceAt("world", 100, 64, 200));
        assertEquals(0, reloaded.getAllInstances().size());
    }
}

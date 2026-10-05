package com.mcp.agent.storage;

import com.google.gson.JsonObject;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.*;

public class ItemStorageTest {

    @Test
    public void testSaveAndReloadItems(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("ItemStorageTest");
        ItemStorage storage = new ItemStorage(tempDir, logger);

        JsonObject item1 = new JsonObject();
        item1.addProperty("id", "ruby_sword");
        item1.addProperty("material", "DIAMOND_SWORD");
        item1.addProperty("display_name", "Ruby Sword");

        storage.saveItem("ruby_sword", item1);

        assertEquals(1, storage.getAllItems().size());
        assertEquals("DIAMOND_SWORD", storage.getItem("ruby_sword").get("material").getAsString());

        // Create new instance pointing to same directory to verify persistence
        ItemStorage reloadedStorage = new ItemStorage(tempDir, logger);
        assertEquals(1, reloadedStorage.getAllItems().size());
        assertNotNull(reloadedStorage.getItem("ruby_sword"));
        assertEquals("Ruby Sword", reloadedStorage.getItem("ruby_sword").get("display_name").getAsString());
    }
}

package com.mcp.agent.pack;

import com.mcp.agent.adapters.oraxen.OraxenPackScanner;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.*;

public class ResourcePackManagerTest {

    @Test
    public void testResourcePackManagerUpdateAndGetters() {
        Logger logger = Logger.getLogger("RPMTest");
        ResourcePackManager manager = new ResourcePackManager(logger);

        assertFalse(manager.hasActivePack());

        manager.updateActivePack(
                "http://127.0.0.1:8000/api/v1/packs/main/download",
                "a9993e364706816aba3e25717850c26c9cd0d89d",
                true,
                "Mandatory Server Pack"
        );

        assertTrue(manager.hasActivePack());
        assertEquals("http://127.0.0.1:8000/api/v1/packs/main/download", manager.getActivePackUrl());
        assertEquals("a9993e364706816aba3e25717850c26c9cd0d89d", manager.getActivePackSha1());
        assertTrue(manager.isRequired());
        assertEquals("Mandatory Server Pack", manager.getPromptMessage());
    }

    @Test
    public void testOraxenPackScannerWithDirectory(@TempDir File tempDir) throws IOException {
        Logger logger = Logger.getLogger("ScannerTest");
        File oraxenFolder = new File(tempDir, "Oraxen");
        File packDir = new File(oraxenFolder, "pack");
        File texturesDir = new File(packDir, "assets/oraxen/textures");
        texturesDir.mkdirs();

        File sampleFile = new File(texturesDir, "sample.png");
        Files.writeString(sampleFile.toPath(), "SAMPLE_TEXTURE_DATA");

        OraxenPackScanner scanner = new OraxenPackScanner(oraxenFolder, logger);
        assertTrue(scanner.hasOraxenPack());

        byte[] zipBytes = scanner.getPackZipBytes();
        assertNotNull(zipBytes);
        assertTrue(zipBytes.length > 0);

        String sha1 = scanner.computeSha1(zipBytes);
        assertNotNull(sha1);
        assertEquals(40, sha1.length());
    }
}

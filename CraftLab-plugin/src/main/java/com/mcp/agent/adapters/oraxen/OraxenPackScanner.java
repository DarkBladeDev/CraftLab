package com.mcp.agent.adapters.oraxen;

import com.google.gson.JsonObject;
import com.mcp.agent.net.AgentWebSocketClient;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HexFormat;
import java.util.logging.Logger;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class OraxenPackScanner {
    private final File oraxenFolder;
    private final Logger logger;
    private String lastSyncedSha1;

    public OraxenPackScanner(File oraxenFolder, Logger logger) {
        this.oraxenFolder = oraxenFolder;
        this.logger = logger;
    }

    public boolean hasOraxenPack() {
        if (oraxenFolder == null || !oraxenFolder.exists()) {
            return false;
        }
        File packDir = new File(oraxenFolder, "pack");
        File packZip = new File(oraxenFolder, "pack.zip");
        return (packDir.exists() && packDir.isDirectory()) || (packZip.exists() && packZip.isFile());
    }

    public byte[] getPackZipBytes() throws IOException {
        File packZip = new File(oraxenFolder, "pack.zip");
        if (packZip.exists() && packZip.isFile()) {
            return Files.readAllBytes(packZip.toPath());
        }

        File packDir = new File(oraxenFolder, "pack");
        if (packDir.exists() && packDir.isDirectory()) {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            try (ZipOutputStream zos = new ZipOutputStream(baos)) {
                zipDirectory(packDir, packDir, zos);
            }
            return baos.toByteArray();
        }

        return null;
    }

    private void zipDirectory(File rootDir, File sourceDir, ZipOutputStream zos) throws IOException {
        File[] files = sourceDir.listFiles();
        if (files == null) return;

        for (File file : files) {
            if (file.isDirectory()) {
                zipDirectory(rootDir, file, zos);
            } else {
                String relativePath = rootDir.toPath().relativize(file.toPath()).toString().replace("\\", "/");
                ZipEntry entry = new ZipEntry(relativePath);
                zos.putNextEntry(entry);
                try (FileInputStream fis = new FileInputStream(file)) {
                    fis.transferTo(zos);
                }
                zos.closeEntry();
            }
        }
    }

    public String computeSha1(byte[] bytes) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-1");
            return HexFormat.of().formatHex(md.digest(bytes));
        } catch (Exception e) {
            return "";
        }
    }

    public boolean scanAndSync(AgentWebSocketClient client) {
        if (!hasOraxenPack() || client == null || !client.isConnected()) {
            return false;
        }

        try {
            byte[] zipBytes = getPackZipBytes();
            if (zipBytes == null || zipBytes.length == 0) {
                return false;
            }

            String sha1 = computeSha1(zipBytes);
            if (sha1.equals(lastSyncedSha1)) {
                // Pack has not changed since last sync
                return false;
            }

            String b64 = Base64.getEncoder().encodeToString(zipBytes);
            JsonObject payload = new JsonObject();
            payload.addProperty("type", "resource_pack:source_sync");
            payload.addProperty("plugin", "oraxen");
            payload.addProperty("sha1", sha1);
            payload.addProperty("zipBase64", b64);

            client.sendEvent("resource_pack:source_sync", payload);
            this.lastSyncedSha1 = sha1;
            if (logger != null) {
                logger.info("Synchronized local Oraxen pack to MCP control plane (SHA-1: " + sha1 + ")");
            }
            return true;
        } catch (Exception e) {
            if (logger != null) {
                logger.warning("Failed to scan and sync Oraxen pack: " + e.getMessage());
            }
            return false;
        }
    }
}

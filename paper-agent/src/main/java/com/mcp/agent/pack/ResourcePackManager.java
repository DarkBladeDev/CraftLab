package com.mcp.agent.pack;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.entity.Player;

import java.util.HexFormat;
import java.util.logging.Logger;

public class ResourcePackManager {
    private final Logger logger;
    private String activePackUrl;
    private String activePackSha1;
    private boolean required = false;
    private String promptMessage = "Server Resource Pack";

    public ResourcePackManager(Logger logger) {
        this.logger = logger;
    }

    public synchronized void updateActivePack(String url, String sha1, boolean required, String promptMessage) {
        this.activePackUrl = url;
        this.activePackSha1 = sha1;
        this.required = required;
        if (promptMessage != null && !promptMessage.isBlank()) {
            this.promptMessage = promptMessage;
        }
        if (logger != null) {
            logger.info("Resource pack updated. URL: " + url + " | SHA-1: " + sha1);
        }
    }

    public synchronized boolean hasActivePack() {
        return activePackUrl != null && !activePackUrl.isBlank();
    }

    public synchronized String getActivePackUrl() {
        return activePackUrl;
    }

    public synchronized String getActivePackSha1() {
        return activePackSha1;
    }

    public synchronized boolean isRequired() {
        return required;
    }

    public synchronized String getPromptMessage() {
        return promptMessage;
    }

    public void applyToPlayer(Player player) {
        if (!hasActivePack()) {
            return;
        }

        try {
            Component prompt = Component.text(promptMessage, NamedTextColor.GOLD);
            if (activePackSha1 != null && activePackSha1.length() == 40) {
                byte[] hashBytes = HexFormat.of().parseHex(activePackSha1);
                player.setResourcePack(activePackUrl, hashBytes, prompt, required);
            } else {
                player.setResourcePack(activePackUrl);
            }
        } catch (Exception e) {
            if (logger != null) {
                logger.warning("Failed to dispatch resource pack to player " + player.getName() + ": " + e.getMessage());
            }
        }
    }

    public int promptAllOnlinePlayers() {
        if (!hasActivePack()) {
            return 0;
        }
        int count = 0;
        for (Player player : Bukkit.getOnlinePlayers()) {
            applyToPlayer(player);
            count++;
        }
        return count;
    }
}

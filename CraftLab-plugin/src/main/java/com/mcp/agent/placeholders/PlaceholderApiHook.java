package com.mcp.agent.placeholders;

import org.bukkit.Bukkit;
import org.bukkit.plugin.Plugin;

import java.util.logging.Logger;

public class PlaceholderApiHook {
    private final Logger logger;

    public PlaceholderApiHook(Logger logger) {
        this.logger = logger;
    }

    public boolean isPlaceholderApiEnabled() {
        return Bukkit.getServer() != null
                && Bukkit.getPluginManager() != null
                && Bukkit.getPluginManager().isPluginEnabled("PlaceholderAPI");
    }

    public String getPlaceholderApiVersion() {
        if (!isPlaceholderApiEnabled()) {
            return "not_installed";
        }
        Plugin plugin = Bukkit.getPluginManager().getPlugin("PlaceholderAPI");
        return plugin != null && plugin.getDescription() != null
                ? plugin.getDescription().getVersion()
                : "unknown";
    }

    public boolean registerExpansion(Plugin plugin, PlaceholderRegistry registry) {
        if (!isPlaceholderApiEnabled()) {
            if (logger != null) {
                logger.info("PlaceholderAPI not detected; skipping %craftlab_...% placeholder expansion registration.");
            }
            return false;
        }

        try {
            CraftLabPlaceholderExpansion expansion = new CraftLabPlaceholderExpansion(plugin, registry);
            boolean registered = expansion.register();
            if (logger != null) {
                if (registered) {
                    logger.info("Registered CraftLab PlaceholderAPI expansion (%craftlab_<domain>_...%).");
                } else {
                    logger.warning("PlaceholderAPI is enabled, but CraftLab expansion registration returned false.");
                }
            }
            return registered;
        } catch (Throwable t) {
            if (logger != null) {
                logger.warning("Failed to register CraftLab PlaceholderAPI expansion: " + t.getMessage());
            }
            return false;
        }
    }
}

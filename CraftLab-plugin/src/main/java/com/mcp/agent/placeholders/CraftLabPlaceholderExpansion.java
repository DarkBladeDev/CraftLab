package com.mcp.agent.placeholders;

import me.clip.placeholderapi.expansion.PlaceholderExpansion;
import org.bukkit.OfflinePlayer;
import org.bukkit.plugin.Plugin;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

public class CraftLabPlaceholderExpansion extends PlaceholderExpansion {
    private final String version;
    private final PlaceholderRegistry registry;

    public CraftLabPlaceholderExpansion(Plugin plugin, PlaceholderRegistry registry) {
        this(plugin != null && plugin.getDescription() != null ? plugin.getDescription().getVersion() : "1.0.0", registry);
    }

    public CraftLabPlaceholderExpansion(String version, PlaceholderRegistry registry) {
        this.version = version != null ? version : "1.0.0";
        this.registry = registry;
    }

    @Override
    public @NotNull String getIdentifier() {
        return "craftlab";
    }

    @Override
    public @NotNull String getAuthor() {
        return "MinecraftContentPlatform";
    }

    @Override
    public @NotNull String getVersion() {
        return version;
    }

    @Override
    public boolean persist() {
        return true;
    }

    @Override
    public boolean canRegister() {
        return true;
    }

    @Override
    public @Nullable String onRequest(OfflinePlayer player, @NotNull String params) {
        if (registry == null) {
            return null;
        }
        return registry.resolve(player, params);
    }
}

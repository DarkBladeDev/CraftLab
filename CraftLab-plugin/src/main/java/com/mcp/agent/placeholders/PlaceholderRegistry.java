package com.mcp.agent.placeholders;

import org.bukkit.OfflinePlayer;

import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class PlaceholderRegistry {
    private final Map<String, PlaceholderProvider> providers = new ConcurrentHashMap<>();

    public void register(PlaceholderProvider provider) {
        if (provider == null || provider.getKey() == null || provider.getKey().isBlank()) {
            return;
        }
        providers.put(provider.getKey().trim().toLowerCase(), provider);
    }

    public PlaceholderProvider getProvider(String key) {
        if (key == null || key.isBlank()) {
            return null;
        }
        return providers.get(key.trim().toLowerCase());
    }

    public Map<String, PlaceholderProvider> getProviders() {
        return Collections.unmodifiableMap(providers);
    }

    /**
     * Routes a raw PlaceholderAPI parameter string ("<domainKey>_<subParams>") to the registered domain provider.
     */
    public String resolve(OfflinePlayer player, String rawParams) {
        if (rawParams == null || rawParams.isBlank()) {
            return null;
        }
        String trimmed = rawParams.trim();
        int underscoreIdx = trimmed.indexOf('_');
        String domainKey;
        String subParams;
        if (underscoreIdx >= 0) {
            domainKey = trimmed.substring(0, underscoreIdx).trim().toLowerCase();
            subParams = trimmed.substring(underscoreIdx + 1);
        } else {
            domainKey = trimmed.toLowerCase();
            subParams = "";
        }

        if (domainKey.isEmpty()) {
            return null;
        }

        PlaceholderProvider provider = providers.get(domainKey);
        if (provider == null) {
            return null;
        }

        return provider.resolve(player, subParams);
    }
}

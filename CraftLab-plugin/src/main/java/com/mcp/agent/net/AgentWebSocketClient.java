package com.mcp.agent.net;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.mcp.agent.storage.ItemStorage;
import org.bukkit.Bukkit;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.UUID;
import java.util.concurrent.*;
import java.util.logging.Logger;

public class AgentWebSocketClient implements WebSocket.Listener {
    private volatile URI gatewayUri;
    private volatile String targetId;
    private volatile String secret;
    private volatile int reconnectIntervalSeconds = 5;
    private volatile int heartbeatIntervalSeconds = 15;
    private final ItemStorage storage;
    private final com.mcp.agent.adapters.oraxen.OraxenCatalogHook oraxenHook;
    private final com.mcp.agent.adapters.oraxen.OraxenItemExporter oraxenExporter;
    private final com.mcp.agent.pack.ResourcePackManager resourcePackManager;
    private final com.mcp.agent.adapters.oraxen.OraxenPackScanner oraxenPackScanner;
    private final com.mcp.agent.props.PropManager propManager;
    private final Logger logger;
    private final Gson gson = new Gson();

    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
    private final HttpClient httpClient = HttpClient.newHttpClient();
    private WebSocket webSocket;
    private ScheduledFuture<?> heartbeatTask;
    private ScheduledFuture<?> reconnectTask;
    private volatile boolean running = false;
    private final StringBuilder messageBuffer = new StringBuilder();

    public AgentWebSocketClient(String gatewayUrl, String targetId, String secret, ItemStorage storage, Logger logger) {
        this(gatewayUrl, targetId, secret, storage, null, null, null, null, null, logger);
    }

    public AgentWebSocketClient(String gatewayUrl, String targetId, String secret, ItemStorage storage,
                                com.mcp.agent.adapters.oraxen.OraxenCatalogHook oraxenHook,
                                com.mcp.agent.adapters.oraxen.OraxenItemExporter oraxenExporter,
                                Logger logger) {
        this(gatewayUrl, targetId, secret, storage, oraxenHook, oraxenExporter, null, null, null, logger);
    }

    public AgentWebSocketClient(String gatewayUrl, String targetId, String secret, ItemStorage storage,
                                com.mcp.agent.adapters.oraxen.OraxenCatalogHook oraxenHook,
                                com.mcp.agent.adapters.oraxen.OraxenItemExporter oraxenExporter,
                                com.mcp.agent.pack.ResourcePackManager resourcePackManager,
                                com.mcp.agent.adapters.oraxen.OraxenPackScanner oraxenPackScanner,
                                Logger logger) {
        this(gatewayUrl, targetId, secret, storage, oraxenHook, oraxenExporter, resourcePackManager, oraxenPackScanner, null, logger);
    }

    public AgentWebSocketClient(String gatewayUrl, String targetId, String secret, ItemStorage storage,
                                com.mcp.agent.adapters.oraxen.OraxenCatalogHook oraxenHook,
                                com.mcp.agent.adapters.oraxen.OraxenItemExporter oraxenExporter,
                                com.mcp.agent.pack.ResourcePackManager resourcePackManager,
                                com.mcp.agent.adapters.oraxen.OraxenPackScanner oraxenPackScanner,
                                com.mcp.agent.props.PropManager propManager,
                                Logger logger) {
        this(gatewayUrl, targetId, secret, 5, 15, storage, oraxenHook, oraxenExporter, resourcePackManager, oraxenPackScanner, propManager, logger);
    }

    public AgentWebSocketClient(String gatewayUrl, String targetId, String secret,
                                int reconnectIntervalSeconds, int heartbeatIntervalSeconds,
                                ItemStorage storage,
                                com.mcp.agent.adapters.oraxen.OraxenCatalogHook oraxenHook,
                                com.mcp.agent.adapters.oraxen.OraxenItemExporter oraxenExporter,
                                com.mcp.agent.pack.ResourcePackManager resourcePackManager,
                                com.mcp.agent.adapters.oraxen.OraxenPackScanner oraxenPackScanner,
                                com.mcp.agent.props.PropManager propManager,
                                Logger logger) {
        this.gatewayUri = URI.create(gatewayUrl != null ? gatewayUrl : "ws://127.0.0.1:8000/ws/agent");
        this.targetId = targetId != null ? targetId : "local-paper-server";
        this.secret = secret != null ? secret : "dev-secret";
        this.reconnectIntervalSeconds = reconnectIntervalSeconds > 0 ? reconnectIntervalSeconds : 5;
        this.heartbeatIntervalSeconds = heartbeatIntervalSeconds > 0 ? heartbeatIntervalSeconds : 15;
        this.storage = storage;
        this.oraxenHook = oraxenHook;
        this.oraxenExporter = oraxenExporter;
        this.resourcePackManager = resourcePackManager;
        this.oraxenPackScanner = oraxenPackScanner;
        this.propManager = propManager;
        this.logger = logger;
    }

    public synchronized void updateConfiguration(String gatewayUrl, String targetId, String secret, int reconnectIntervalSeconds, int heartbeatIntervalSeconds) {
        try {
            if (gatewayUrl != null && !gatewayUrl.isBlank()) {
                this.gatewayUri = URI.create(gatewayUrl);
            }
        } catch (Exception e) {
            logger.severe("Invalid gateway URL '" + gatewayUrl + "': " + e.getMessage());
        }
        if (targetId != null && !targetId.isBlank()) {
            this.targetId = targetId;
        }
        if (secret != null) {
            this.secret = secret;
        }
        if (reconnectIntervalSeconds > 0) {
            this.reconnectIntervalSeconds = reconnectIntervalSeconds;
        }
        if (heartbeatIntervalSeconds > 0) {
            this.heartbeatIntervalSeconds = heartbeatIntervalSeconds;
        }
    }

    public synchronized void reconnect() {
        if (!running) {
            start();
            return;
        }
        if (heartbeatTask != null) {
            heartbeatTask.cancel(true);
            heartbeatTask = null;
        }
        if (reconnectTask != null) {
            reconnectTask.cancel(true);
            reconnectTask = null;
        }
        if (webSocket != null) {
            WebSocket oldWs = webSocket;
            webSocket = null;
            try {
                oldWs.sendClose(WebSocket.NORMAL_CLOSURE, "Reload requested");
            } catch (Exception ignored) {
            }
        }
        messageBuffer.setLength(0);
        connect();
    }

    public URI getGatewayUri() {
        return gatewayUri;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getSecret() {
        return secret;
    }

    public int getReconnectIntervalSeconds() {
        return reconnectIntervalSeconds;
    }

    public int getHeartbeatIntervalSeconds() {
        return heartbeatIntervalSeconds;
    }

    public synchronized void start() {
        if (running) return;
        running = true;
        connect();
    }

    public synchronized void stop() {
        running = false;
        if (heartbeatTask != null) {
            heartbeatTask.cancel(true);
            heartbeatTask = null;
        }
        if (reconnectTask != null) {
            reconnectTask.cancel(true);
            reconnectTask = null;
        }
        if (webSocket != null) {
            WebSocket oldWs = webSocket;
            webSocket = null;
            try {
                oldWs.sendClose(WebSocket.NORMAL_CLOSURE, "Plugin disabled");
            } catch (Exception ignored) {
            }
        }
        scheduler.shutdownNow();
    }

    public boolean isConnected() {
        return webSocket != null && !webSocket.isInputClosed() && !webSocket.isOutputClosed();
    }

    private synchronized void connect() {
        if (!running) return;
        if (reconnectTask != null) {
            reconnectTask.cancel(false);
            reconnectTask = null;
        }
        logger.info("Connecting to MCP Gateway: " + gatewayUri);
        httpClient.newWebSocketBuilder()
                .connectTimeout(java.time.Duration.ofSeconds(5))
                .buildAsync(gatewayUri, this)
                .whenComplete((ws, throwable) -> {
                    if (throwable != null) {
                        logger.warning("Failed to connect to gateway: " + throwable.getMessage() + ". Retrying in " + reconnectIntervalSeconds + "s...");
                        scheduleReconnect();
                    }
                });
    }

    private synchronized void scheduleReconnect() {
        if (!running) return;
        if (heartbeatTask != null) {
            heartbeatTask.cancel(true);
            heartbeatTask = null;
        }
        if (reconnectTask != null && !reconnectTask.isDone()) {
            return;
        }
        reconnectTask = scheduler.schedule(this::connect, reconnectIntervalSeconds, TimeUnit.SECONDS);
    }

    @Override
    public void onOpen(WebSocket webSocket) {
        this.webSocket = webSocket;
        logger.info("Connected to MCP Gateway successfully!");
        webSocket.request(1);

        sendHello();
        startHeartbeats();
        if (oraxenPackScanner != null) {
            oraxenPackScanner.scanAndSync(this);
        }
    }

    public void sendEvent(String eventType, JsonObject payload) {
        if (!isConnected()) return;
        JsonObject envelope = new JsonObject();
        envelope.addProperty("protocolVersion", "1.0");
        envelope.addProperty("messageType", "event");
        envelope.addProperty("messageId", "msg-event-" + UUID.randomUUID());
        envelope.addProperty("targetId", targetId);
        envelope.addProperty("sentAt", Instant.now().toString());
        envelope.add("payload", payload);

        webSocket.sendText(gson.toJson(envelope), true);
    }

    public com.mcp.agent.pack.ResourcePackManager getResourcePackManager() {
        return resourcePackManager;
    }

    private void sendHello() {
        JsonObject payload = new JsonObject();
        payload.addProperty("agentVersion", "1.1.0");
        payload.addProperty("minecraftVersion", Bukkit.getMinecraftVersion());
        payload.addProperty("paperVersion", Bukkit.getVersion());
        payload.addProperty("secret", secret);

        com.google.gson.JsonArray detectedPlugins = new com.google.gson.JsonArray();
        if (oraxenHook != null && oraxenHook.isOraxenEnabled()) {
            JsonObject oraxenObj = new JsonObject();
            oraxenObj.addProperty("name", "Oraxen");
            oraxenObj.addProperty("version", oraxenHook.getOraxenVersion());
            oraxenObj.addProperty("enabled", true);
            detectedPlugins.add(oraxenObj);

            java.util.List<JsonObject> items = oraxenHook.getDiscoveredItems();
            if (!items.isEmpty()) {
                JsonObject manifest = new JsonObject();
                manifest.addProperty("source", "oraxen");
                com.google.gson.JsonArray itemsArr = new com.google.gson.JsonArray();
                for (JsonObject it : items) {
                    itemsArr.add(it);
                }
                manifest.add("items", itemsArr);
                payload.add("catalogManifest", manifest);
            }
        }
        payload.add("detectedPlugins", detectedPlugins);

        JsonObject envelope = new JsonObject();
        envelope.addProperty("protocolVersion", "1.0");
        envelope.addProperty("messageType", "hello");
        envelope.addProperty("messageId", "msg-hello-" + UUID.randomUUID());
        envelope.addProperty("targetId", targetId);
        envelope.addProperty("sentAt", Instant.now().toString());
        envelope.add("payload", payload);

        webSocket.sendText(gson.toJson(envelope), true);
    }

    private void startHeartbeats() {
        if (heartbeatTask != null) {
            heartbeatTask.cancel(true);
        }
        heartbeatTask = scheduler.scheduleAtFixedRate(() -> {
            if (isConnected()) {
                JsonObject payload = new JsonObject();
                payload.addProperty("type", "heartbeat");

                JsonObject envelope = new JsonObject();
                envelope.addProperty("protocolVersion", "1.0");
                envelope.addProperty("messageType", "event");
                envelope.addProperty("messageId", "msg-hb-" + UUID.randomUUID());
                envelope.addProperty("targetId", targetId);
                envelope.addProperty("sentAt", Instant.now().toString());
                envelope.add("payload", payload);

                webSocket.sendText(gson.toJson(envelope), true);
            }
        }, heartbeatIntervalSeconds, heartbeatIntervalSeconds, TimeUnit.SECONDS);
    }

    @Override
    public CompletionStage<?> onText(WebSocket webSocket, CharSequence data, boolean last) {
        messageBuffer.append(data);
        if (last) {
            String fullMessage = messageBuffer.toString();
            messageBuffer.setLength(0);
            handleIncomingMessage(fullMessage);
        }
        webSocket.request(1);
        return null;
    }

    private void handleIncomingMessage(String text) {
        try {
            JsonObject env = gson.fromJson(text, JsonObject.class);
            String messageType = env.get("messageType").getAsString();

            if ("event".equals(messageType)) {
                JsonObject payload = env.getAsJsonObject("payload");
                String type = payload.has("type") ? payload.get("type").getAsString() : "";
                if ("resource_pack:ready".equals(type) || "resource_pack.ready".equals(type)) {
                    String url = payload.get("url").getAsString();
                    String sha1 = payload.get("sha1").getAsString();
                    boolean req = payload.has("required") && payload.get("required").getAsBoolean();
                    String prompt = payload.has("prompt") ? payload.get("prompt").getAsString() : "Server Resource Pack";
                    if (resourcePackManager != null) {
                        resourcePackManager.updateActivePack(url, sha1, req, prompt);
                    }
                    return;
                }
            }

            if ("request".equals(messageType)) {
                JsonObject payload = env.getAsJsonObject("payload");
                String action = payload.get("action").getAsString();
                String correlationId = env.has("correlationId") ? env.get("correlationId").getAsString() : env.get("messageId").getAsString();

                if ("catalog:refresh".equals(action)) {
                    JsonObject respPayload = new JsonObject();
                    respPayload.addProperty("status", "success");
                    respPayload.addProperty("source", "oraxen");
                    com.google.gson.JsonArray itemsArr = new com.google.gson.JsonArray();
                    if (oraxenHook != null) {
                        for (JsonObject it : oraxenHook.getDiscoveredItems()) {
                            itemsArr.add(it);
                        }
                    }
                    respPayload.add("items", itemsArr);

                    JsonObject respEnv = new JsonObject();
                    respEnv.addProperty("protocolVersion", "1.0");
                    respEnv.addProperty("messageType", "response");
                    respEnv.addProperty("messageId", "msg-resp-" + UUID.randomUUID());
                    respEnv.addProperty("correlationId", correlationId);
                    respEnv.addProperty("targetId", targetId);
                    respEnv.addProperty("sentAt", Instant.now().toString());
                    respEnv.add("payload", respPayload);

                    webSocket.sendText(gson.toJson(respEnv), true);
                    return;
                }

                if ("create_or_update_item".equals(action)) {
                    JsonObject itemData = payload.getAsJsonObject("item");
                    String itemId = itemData.get("id").getAsString();

                    // If export_format is oraxen, delegate to oraxenExporter
                    if (oraxenExporter != null && itemData.has("export_format")
                            && "oraxen".equalsIgnoreCase(itemData.get("export_format").getAsString())) {
                        oraxenExporter.exportItem(itemData);
                    }

                    storage.saveItem(itemId, itemData);
                    logger.info("Successfully applied item '" + itemId + "' via MCP deployment.");

                    // Respond with success
                    JsonObject respPayload = new JsonObject();
                    respPayload.addProperty("status", "applied");
                    respPayload.addProperty("success", true);
                    respPayload.addProperty("itemId", itemId);

                    JsonObject respEnv = new JsonObject();
                    respEnv.addProperty("protocolVersion", "1.0");
                    respEnv.addProperty("messageType", "response");
                    respEnv.addProperty("messageId", "msg-resp-" + UUID.randomUUID());
                    respEnv.addProperty("correlationId", correlationId);
                    respEnv.addProperty("targetId", targetId);
                    respEnv.addProperty("sentAt", Instant.now().toString());
                    respEnv.add("payload", respPayload);

                    webSocket.sendText(gson.toJson(respEnv), true);
                    return;
                }

                if ("create_or_update_block".equals(action) || "create_or_update_prop".equals(action)) {
                    JsonObject blockData = null;
                    if (payload.has("block") && payload.get("block").isJsonObject()) {
                        blockData = payload.getAsJsonObject("block");
                    } else if (payload.has("prop") && payload.get("prop").isJsonObject()) {
                        blockData = payload.getAsJsonObject("prop");
                    } else if (payload.has("item") && payload.get("item").isJsonObject()) {
                        blockData = payload.getAsJsonObject("item");
                    } else if (payload.has("payload") && payload.get("payload").isJsonObject()) {
                        blockData = payload.getAsJsonObject("payload");
                    }

                    if (blockData != null) {
                        com.mcp.agent.props.PropDefinition def = com.mcp.agent.props.PropDefinition.fromJson(blockData);
                        if (propManager != null) {
                            propManager.registerDefinition(def);
                        }
                        logger.info("Successfully applied block/prop '" + def.getId() + "' via MCP deployment.");

                        JsonObject respPayload = new JsonObject();
                        respPayload.addProperty("status", "applied");
                        respPayload.addProperty("success", true);
                        respPayload.addProperty("blockId", def.getId());
                        respPayload.addProperty("resourceId", def.getId());

                        JsonObject respEnv = new JsonObject();
                        respEnv.addProperty("protocolVersion", "1.0");
                        respEnv.addProperty("messageType", "response");
                        respEnv.addProperty("messageId", "msg-resp-" + UUID.randomUUID());
                        respEnv.addProperty("correlationId", correlationId);
                        respEnv.addProperty("targetId", targetId);
                        respEnv.addProperty("sentAt", Instant.now().toString());
                        respEnv.add("payload", respPayload);

                        webSocket.sendText(gson.toJson(respEnv), true);
                        return;
                    }
                }
            }
        } catch (Exception e) {
            logger.severe("Error handling gateway message: " + e.getMessage());
        }
    }

    @Override
    public CompletionStage<?> onClose(WebSocket webSocket, int statusCode, String reason) {
        if (webSocket != this.webSocket) {
            return null;
        }
        this.webSocket = null;
        logger.warning("Gateway WebSocket closed (" + statusCode + "): " + reason);
        scheduleReconnect();
        return null;
    }

    @Override
    public void onError(WebSocket webSocket, Throwable error) {
        if (webSocket != this.webSocket) {
            return;
        }
        logger.warning("Gateway WebSocket error: " + error.getMessage());
        scheduleReconnect();
    }
}

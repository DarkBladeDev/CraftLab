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
    private final URI gatewayUri;
    private final String targetId;
    private final String secret;
    private final ItemStorage storage;
    private final Logger logger;
    private final Gson gson = new Gson();

    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
    private final HttpClient httpClient = HttpClient.newHttpClient();
    private WebSocket webSocket;
    private ScheduledFuture<?> heartbeatTask;
    private volatile boolean running = false;
    private final StringBuilder messageBuffer = new StringBuilder();

    public AgentWebSocketClient(String gatewayUrl, String targetId, String secret, ItemStorage storage, Logger logger) {
        this.gatewayUri = URI.create(gatewayUrl);
        this.targetId = targetId;
        this.secret = secret;
        this.storage = storage;
        this.logger = logger;
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
        }
        if (webSocket != null) {
            webSocket.sendClose(WebSocket.NORMAL_CLOSURE, "Plugin disabled");
        }
        scheduler.shutdownNow();
    }

    public boolean isConnected() {
        return webSocket != null && !webSocket.isInputClosed() && !webSocket.isOutputClosed();
    }

    private void connect() {
        if (!running) return;
        logger.info("Connecting to MCP Gateway: " + gatewayUri);
        httpClient.newWebSocketBuilder()
                .connectTimeout(java.time.Duration.ofSeconds(5))
                .buildAsync(gatewayUri, this)
                .whenComplete((ws, throwable) -> {
                    if (throwable != null) {
                        logger.warning("Failed to connect to gateway: " + throwable.getMessage() + ". Retrying in 5s...");
                        scheduleReconnect();
                    }
                });
    }

    private void scheduleReconnect() {
        if (!running) return;
        if (heartbeatTask != null) {
            heartbeatTask.cancel(true);
        }
        scheduler.schedule(this::connect, 5, TimeUnit.SECONDS);
    }

    @Override
    public void onOpen(WebSocket webSocket) {
        this.webSocket = webSocket;
        logger.info("Connected to MCP Gateway successfully!");
        webSocket.request(1);

        sendHello();
        startHeartbeats();
    }

    private void sendHello() {
        JsonObject payload = new JsonObject();
        payload.addProperty("agentVersion", "1.0.0");
        payload.addProperty("minecraftVersion", Bukkit.getMinecraftVersion());
        payload.addProperty("paperVersion", Bukkit.getVersion());
        payload.addProperty("secret", secret);

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
        }, 15, 15, TimeUnit.SECONDS);
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

            if ("request".equals(messageType)) {
                JsonObject payload = env.getAsJsonObject("payload");
                String action = payload.get("action").getAsString();
                String correlationId = env.has("correlationId") ? env.get("correlationId").getAsString() : env.get("messageId").getAsString();

                if ("create_or_update_item".equals(action)) {
                    JsonObject itemData = payload.getAsJsonObject("item");
                    String itemId = itemData.get("id").getAsString();

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
                }
            }
        } catch (Exception e) {
            logger.severe("Error handling gateway message: " + e.getMessage());
        }
    }

    @Override
    public CompletionStage<?> onClose(WebSocket webSocket, int statusCode, String reason) {
        logger.warning("Gateway WebSocket closed (" + statusCode + "): " + reason);
        scheduleReconnect();
        return null;
    }

    @Override
    public void onError(WebSocket webSocket, Throwable error) {
        logger.warning("Gateway WebSocket error: " + error.getMessage());
        scheduleReconnect();
    }
}

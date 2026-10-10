package com.mcp.agent.props;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.util.*;

public class PropDefinition {

    public static class PropStateSound {
        private String key;
        private float volume = 1.0f;
        private float pitch = 1.0f;

        public PropStateSound() {}

        public PropStateSound(String key, float volume, float pitch) {
            this.key = key;
            this.volume = volume;
            this.pitch = pitch;
        }

        public String getKey() {
            return key;
        }

        public void setKey(String key) {
            this.key = key;
        }

        public float getVolume() {
            return volume;
        }

        public void setVolume(float volume) {
            this.volume = volume;
        }

        public float getPitch() {
            return pitch;
        }

        public void setPitch(float pitch) {
            this.pitch = pitch;
        }
    }

    public static class PropState {
        private String name;
        private String blockModel;
        private int lightLevel = 0;
        private PropStateSound sound;
        private String hitboxType;
        private String nextState;

        public PropState() {}

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getBlockModel() {
            return blockModel;
        }

        public void setBlockModel(String blockModel) {
            this.blockModel = blockModel;
        }

        public int getLightLevel() {
            return lightLevel;
        }

        public void setLightLevel(int lightLevel) {
            this.lightLevel = lightLevel;
        }

        public PropStateSound getSound() {
            return sound;
        }

        public void setSound(PropStateSound sound) {
            this.sound = sound;
        }

        public String getHitboxType() {
            return hitboxType;
        }

        public void setHitboxType(String hitboxType) {
            this.hitboxType = hitboxType;
        }

        public String getNextState() {
            return nextState;
        }

        public void setNextState(String nextState) {
            this.nextState = nextState;
        }
    }

    private String id;
    private String displayName;
    private String mode = "display_prop";
    private String itemModel;
    private String blockModel;
    private List<Float> scale = Arrays.asList(1.0f, 1.0f, 1.0f);
    private List<Float> translation = Arrays.asList(0.0f, 0.0f, 0.0f);
    private String hitboxType = "solid";
    private List<int[]> hitboxOffsets = new ArrayList<>();
    private String interactionType = "none";
    private float seatHeight = 0.5f;
    private float hardness = 1.0f;
    private String toolType = "AXE";
    private String dropItemId;
    private String defaultState = "default";
    private Map<String, PropState> states = new LinkedHashMap<>();

    public PropDefinition() {
        hitboxOffsets.add(new int[]{0, 0, 0});
    }

    public PropDefinition(String id, String displayName, String itemModel) {
        this(id, displayName, itemModel, itemModel);
    }

    public PropDefinition(String id, String displayName, String itemModel, String blockModel) {
        this();
        this.id = id;
        this.displayName = displayName;
        this.itemModel = itemModel;
        this.blockModel = blockModel;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }

    public String getMode() {
        return mode;
    }

    public void setMode(String mode) {
        this.mode = mode;
    }

    public String getItemModel() {
        return itemModel;
    }

    public void setItemModel(String itemModel) {
        this.itemModel = itemModel;
    }

    public String getBlockModel() {
        return (blockModel != null && !blockModel.isEmpty()) ? blockModel : itemModel;
    }

    public void setBlockModel(String blockModel) {
        this.blockModel = blockModel;
    }

    public List<Float> getScale() {
        return scale;
    }

    public void setScale(List<Float> scale) {
        this.scale = scale;
    }

    public List<Float> getTranslation() {
        return translation;
    }

    public void setTranslation(List<Float> translation) {
        this.translation = translation;
    }

    public String getHitboxType() {
        return hitboxType;
    }

    public void setHitboxType(String hitboxType) {
        this.hitboxType = hitboxType;
    }

    public List<int[]> getHitboxOffsets() {
        return hitboxOffsets;
    }

    public void setHitboxOffsets(List<int[]> hitboxOffsets) {
        this.hitboxOffsets = hitboxOffsets;
    }

    public String getInteractionType() {
        return interactionType;
    }

    public void setInteractionType(String interactionType) {
        this.interactionType = interactionType;
    }

    public float getSeatHeight() {
        return seatHeight;
    }

    public void setSeatHeight(float seatHeight) {
        this.seatHeight = seatHeight;
    }

    public float getHardness() {
        return hardness;
    }

    public void setHardness(float hardness) {
        this.hardness = hardness;
    }

    public String getToolType() {
        return toolType;
    }

    public void setToolType(String toolType) {
        this.toolType = toolType;
    }

    public String getDropItemId() {
        return dropItemId;
    }

    public void setDropItemId(String dropItemId) {
        this.dropItemId = dropItemId;
    }

    public String getDefaultState() {
        return defaultState != null && !defaultState.isEmpty() ? defaultState : "default";
    }

    public void setDefaultState(String defaultState) {
        this.defaultState = defaultState;
    }

    public Map<String, PropState> getStates() {
        return states != null ? states : Collections.emptyMap();
    }

    public void setStates(Map<String, PropState> states) {
        this.states = states != null ? states : new LinkedHashMap<>();
    }

    public PropState getState(String stateKey) {
        if (stateKey == null || states == null) return null;
        return states.get(stateKey);
    }

    public String getBlockModelForState(String stateKey) {
        PropState state = getState(stateKey);
        if (state != null && state.getBlockModel() != null && !state.getBlockModel().trim().isEmpty()) {
            return state.getBlockModel().trim();
        }
        return getBlockModel();
    }

    public static PropDefinition fromJson(com.google.gson.JsonObject obj) {
        PropDefinition def = new PropDefinition();
        if (obj.has("id")) def.setId(obj.get("id").getAsString());
        if (obj.has("display_name")) def.setDisplayName(obj.get("display_name").getAsString());
        else if (obj.has("displayName")) def.setDisplayName(obj.get("displayName").getAsString());

        if (obj.has("mode")) def.setMode(obj.get("mode").getAsString());
        if (obj.has("item_model") && !obj.get("item_model").isJsonNull()) def.setItemModel(obj.get("item_model").getAsString());
        else if (obj.has("itemModel") && !obj.get("itemModel").isJsonNull()) def.setItemModel(obj.get("itemModel").getAsString());

        if (obj.has("block_model") && !obj.get("block_model").isJsonNull()) def.setBlockModel(obj.get("block_model").getAsString());
        else if (obj.has("blockModel") && !obj.get("blockModel").isJsonNull()) def.setBlockModel(obj.get("blockModel").getAsString());

        Gson gson = new Gson();
        if (obj.has("scale") && obj.get("scale").isJsonArray()) {
            List<Float> scale = gson.fromJson(obj.get("scale"), new TypeToken<List<Float>>(){}.getType());
            def.setScale(scale);
        }
        if (obj.has("translation") && obj.get("translation").isJsonArray()) {
            List<Float> translation = gson.fromJson(obj.get("translation"), new TypeToken<List<Float>>(){}.getType());
            def.setTranslation(translation);
        }
        if (obj.has("hitbox_type")) def.setHitboxType(obj.get("hitbox_type").getAsString());
        else if (obj.has("hitboxType")) def.setHitboxType(obj.get("hitboxType").getAsString());

        if (obj.has("hitbox_offsets") && obj.get("hitbox_offsets").isJsonArray()) {
            List<int[]> offsets = gson.fromJson(obj.get("hitbox_offsets"), new TypeToken<List<int[]>>(){}.getType());
            def.setHitboxOffsets(offsets);
        } else if (obj.has("hitboxOffsets") && obj.get("hitboxOffsets").isJsonArray()) {
            List<int[]> offsets = gson.fromJson(obj.get("hitboxOffsets"), new TypeToken<List<int[]>>(){}.getType());
            def.setHitboxOffsets(offsets);
        }

        if (obj.has("interaction_type") && !obj.get("interaction_type").isJsonNull()) def.setInteractionType(obj.get("interaction_type").getAsString());
        else if (obj.has("interactionType") && !obj.get("interactionType").isJsonNull()) def.setInteractionType(obj.get("interactionType").getAsString());

        if (obj.has("seat_height")) def.setSeatHeight(obj.get("seat_height").getAsFloat());
        else if (obj.has("seatHeight")) def.setSeatHeight(obj.get("seatHeight").getAsFloat());

        if (obj.has("hardness")) def.setHardness(obj.get("hardness").getAsFloat());

        if (obj.has("tool_type")) def.setToolType(obj.get("tool_type").getAsString());
        else if (obj.has("toolType")) def.setToolType(obj.get("toolType").getAsString());

        if (obj.has("drop_item_id") && !obj.get("drop_item_id").isJsonNull()) def.setDropItemId(obj.get("drop_item_id").getAsString());
        else if (obj.has("dropItemId") && !obj.get("dropItemId").isJsonNull()) def.setDropItemId(obj.get("dropItemId").getAsString());

        if (obj.has("default_state") && !obj.get("default_state").isJsonNull()) def.setDefaultState(obj.get("default_state").getAsString());
        else if (obj.has("defaultState") && !obj.get("defaultState").isJsonNull()) def.setDefaultState(obj.get("defaultState").getAsString());

        if (obj.has("states") && obj.get("states").isJsonObject()) {
            com.google.gson.JsonObject statesObj = obj.getAsJsonObject("states");
            Map<String, PropState> stateMap = new LinkedHashMap<>();
            for (String key : statesObj.keySet()) {
                com.google.gson.JsonElement el = statesObj.get(key);
                if (el.isJsonObject()) {
                    com.google.gson.JsonObject sObj = el.getAsJsonObject();
                    PropState s = new PropState();
                    if (sObj.has("name") && !sObj.get("name").isJsonNull()) s.setName(sObj.get("name").getAsString());
                    if (sObj.has("block_model") && !sObj.get("block_model").isJsonNull()) s.setBlockModel(sObj.get("block_model").getAsString());
                    else if (sObj.has("blockModel") && !sObj.get("blockModel").isJsonNull()) s.setBlockModel(sObj.get("blockModel").getAsString());

                    if (sObj.has("light_level")) s.setLightLevel(sObj.get("light_level").getAsInt());
                    else if (sObj.has("lightLevel")) s.setLightLevel(sObj.get("lightLevel").getAsInt());

                    if (sObj.has("hitbox_type") && !sObj.get("hitbox_type").isJsonNull()) s.setHitboxType(sObj.get("hitbox_type").getAsString());
                    else if (sObj.has("hitboxType") && !sObj.get("hitboxType").isJsonNull()) s.setHitboxType(sObj.get("hitboxType").getAsString());

                    if (sObj.has("next_state") && !sObj.get("next_state").isJsonNull()) s.setNextState(sObj.get("next_state").getAsString());
                    else if (sObj.has("nextState") && !sObj.get("nextState").isJsonNull()) s.setNextState(sObj.get("nextState").getAsString());

                    if (sObj.has("sound") && sObj.get("sound").isJsonObject()) {
                        com.google.gson.JsonObject sndObj = sObj.getAsJsonObject("sound");
                        PropStateSound snd = new PropStateSound();
                        if (sndObj.has("key") && !sndObj.get("key").isJsonNull()) snd.setKey(sndObj.get("key").getAsString());
                        if (sndObj.has("volume")) snd.setVolume(sndObj.get("volume").getAsFloat());
                        if (sndObj.has("pitch")) snd.setPitch(sndObj.get("pitch").getAsFloat());
                        s.setSound(snd);
                    }
                    stateMap.put(key, s);
                }
            }
            def.setStates(stateMap);
        }

        return def;
    }
}

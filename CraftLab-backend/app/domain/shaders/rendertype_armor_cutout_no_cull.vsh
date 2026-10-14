#version 150

#moj_import <light.glsl>

in vec3 Position;
in vec4 Color;
in vec2 UV0;
in ivec2 UV1;
in ivec2 UV2;
in vec3 Normal;

uniform sampler2D Sampler0;
uniform mat4 ModelViewMat;
uniform mat4 ProjMat;
uniform vec4 ColorModulator;
uniform vec3 Light0_Direction;
uniform vec3 Light1_Direction;

out vec4 vertexColor;
out vec2 texCoord0;

#ifndef TOTAL_LAYERS
#define TOTAL_LAYERS 1
#endif

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);

    ivec2 texSize = textureSize(Sampler0, 0);
    float total = float(TOTAL_LAYERS + 1);

    // Check if texture is an atlas (height > 32 indicates a multi-layer composite atlas)
    bool isAtlas = (texSize.y > 32 && TOTAL_LAYERS > 0);

    if (isAtlas) {
        int r = int(round(Color.r * 255.0));
        int g = int(round(Color.g * 255.0));
        int b = int(round(Color.b * 255.0));
        int id = r * 65536 + g * 256 + b;

        if (id >= 1 && id <= TOTAL_LAYERS) {
            // Custom equipment layer: untinted texture from allocated atlas slice
            texCoord0 = vec2(UV0.x, (UV0.y + float(id)) / total);
            vertexColor = minecraft_mix_light(Light0_Direction, Light1_Direction, Normal, vec4(1.0, 1.0, 1.0, 1.0)) * ColorModulator;
        } else {
            // Standard leather armor: slice 0 with vanilla dye color tint
            texCoord0 = vec2(UV0.x, UV0.y / total);
            vertexColor = minecraft_mix_light(Light0_Direction, Light1_Direction, Normal, Color) * ColorModulator;
        }
    } else {
        // Standard vanilla armor (diamond, iron, gold, chainmail, netherite): standard UV mapping
        texCoord0 = UV0;
        vertexColor = minecraft_mix_light(Light0_Direction, Light1_Direction, Normal, Color) * ColorModulator;
    }
}

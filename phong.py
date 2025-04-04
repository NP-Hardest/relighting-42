import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
# import imageio.v2 as imageio

# def load_hdr_image(path):
#     # imageio returns an array with HDR values.
#     return np.array(imageio.imread(path)).astype(np.float32)


def load_image(path):
    return np.array(Image.open(path)) / 255.0

def save_image(image, path):
    Image.fromarray((image * 255).astype('uint8')).save(path)

def srgb_to_linear(srgb):
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)

def linear_to_srgb(linear):
    return np.where(
        linear <= 0.0031308,
        linear * 12.92,
        1.055 * (linear ** (1/2.4)) - 0.055
    )

def normalize(v):
    norm = np.linalg.norm(v, axis=-1, keepdims=True)
    return np.where(norm > 0, v / norm, 0)

def reflect(incident, normal):
    return incident - 2 * np.sum(incident * normal, axis=-1, keepdims=True) * normal

def relight_with_specular_map(albedo_path, normal_path, specular_map_path, alpha_path, output_path):
    albedo_srgb = load_image(albedo_path)
    if albedo_srgb.shape[-1] == 4:
        albedo_srgb = albedo_srgb[..., :3]
    albedo_linear = srgb_to_linear(albedo_srgb)

    normal_png = load_image(normal_path)
    normal = 2.0 * normal_png - 1.0  
    normal = normalize(normal)

    specular_map = load_image(specular_map_path)
    mask = load_image(alpha_path)

    lights = [
        {
            'type': 'directional',
            'direction': normalize(np.array([-0.7, 0.7, 0.5])),  # top-left direction
            'color': np.array([1, 1, 1]),
            'intensity': 1
        },
        {
            'type': 'directional',
            'direction': normalize(np.array([0.7, 0.7, 0.5])),  # top-right direction
            'color': np.array([0, 1, 0]),
            'intensity': 1
        }
    ]
    
    # Ambient term.
    ambient = np.array([0.15, 0.2, 0.25])

    shininess = 10.0                #can change this

    height, width, _ = albedo_linear.shape
    result = np.zeros((height, width, 3))

    view_dir = np.array([0, 0, 1])

    for y in range(height):
        for x in range(width):

            if mask[y, x] <= 0.99:
                result[y, x] = np.zeros(3)
                continue


            albedo_pixel = albedo_linear[y, x]
            normal_pixel = normal[y, x]
            specular_strength_pixel = specular_map[y, x] * 0.1

            diffuse = np.zeros(3)
            specular = np.zeros(3)

            for light in lights:
                l_dir = light['direction']
                ndotl = max(np.dot(normal_pixel, l_dir), 0.0)
                diffuse += ndotl * light['intensity'] * light['color']

                h = normalize(view_dir + l_dir)
                ndoth = max(np.dot(normal_pixel, h), 0.0)
                specular += (ndoth ** shininess) * specular_strength_pixel * light['color']

            ambient_term = ambient * albedo_pixel
            result[y, x] = (diffuse * albedo_pixel) + ambient_term + specular

    result = np.clip(result, 0, 1)
    result_srgb = linear_to_srgb(result)
    save_image(result_srgb, output_path)

relight_with_specular_map(
    albedo_path="inputs/albedo.png",
    normal_path="inputs/normal.png",
    specular_map_path="inputs/specular.png",
    alpha_path="inputs/alpha.png",
    output_path="output_phong.png"
)

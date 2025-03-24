from enum import IntEnum

from .generated import glTF_generated as flat


class AccessorType(IntEnum):
    SCALAR = 0
    VEC2 = 1
    VEC3 = 2
    VEC4 = 3
    MAT2 = 4
    MAT3 = 5
    MAT4 = 6


class AnimationChannelTargetPath(IntEnum):
    translation = 0
    rotation = 1
    scale = 2
    weights = 3


class AnimationSamplerInterpolationAlgorithm(IntEnum):
    LINEAR = 0
    STEP = 1
    CATMULLROMSPLINE = 2
    CUBICSPLINE = 3


class CameraType(IntEnum):
    perspective = 0
    orthographic = 1


# str - Strings
# bytes - FlexBuffers
# int - Integer
# float - Numbers
# dicts - Structs
gltf_schema = {
    "_type": flat.Root,
    "accessors": [
        {
            "_type": flat.Accessor,
            "bufferView": int,
            "byteOffset": int,
            "componentType": int,
            "normalized": (bool, False),
            "count": int,
            "type": AccessorType,
            "max": [float],
            "min": [float],
            "sparse": {
                "_type": flat.AccessorSparse,
                "count": int,
                "indices": {
                    "_type": flat.AccessorSparseIndices,
                    "bufferView": int,
                    "byteOffset": int,
                    "componentType": int,
                    "extensions": bytes,
                    "extras": bytes,
                },
                "values": {
                    "_type": flat.AccessorSparseValues,
                    "bufferView": int,
                    "byteOffset": int,
                    "extensions": bytes,
                    "extras": bytes,
                },
                "extensions": bytes,
                "extras": bytes,
            },
            "name": str,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "animations": [
        {
            "_type": flat.Animation,
            "name": str,
            "channels": [
                {
                    "_type": flat.AnimationChannel,
                    "sampler": int,
                    "target": {
                        "_type": flat.AnimationChannelTarget,
                        "node": int,
                        "path": AnimationChannelTargetPath,
                        "extensions": bytes,
                        "extras": bytes,
                    },
                    "extensions": bytes,
                    "extras": bytes,
                }
            ],
            "samplers": [
                {
                    "_type": flat.AnimationSampler,
                    "input": int,
                    "interpolation": (
                        AnimationSamplerInterpolationAlgorithm,
                        AnimationSamplerInterpolationAlgorithm.LINEAR,
                    ),
                    "output": int,
                    "extensions": bytes,
                    "extras": bytes,
                }
            ],
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "asset": {
        "_type": flat.Asset,
        "name": str,
        "copyright": str,
        "generator": str,
        "version": str,
        "minVersion": str,
        "extensions": bytes,
        "extras": bytes,
    },
    "buffers": [
        {
            "_type": flat.Buffer,
            "name": str,
            "uri": str,
            "byteLength": int,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "bufferViews": [
        {
            "_type": flat.BufferView,
            "name": str,
            "buffer": int,
            "byteOffset": int,
            "byteLength": int,
            "byteStride": (int, 0),
            "target": (int, 34962),
            "extensions": bytes,
            # "extras": bytes, # struct.error :\
        }
    ],
    "extensionsRequired": [str],
    "extensionsUsed": [str],
    "cameras": [
        {
            "_type": flat.Camera,
            "name": str,
            "type": CameraType,
            "orthographic": {
                "_type": flat.CameraOrthographic,
                "xmag": float,
                "ymag": float,
                "zfar": float,
                "znear": float,
                "extensions": bytes,
                "extras": bytes,
            },
            "perspective": {
                "_type": flat.CameraPerspective,
                "aspectRatio": float,
                "yfov": float,
                "zfar": float,
                "znear": float,
                "extensions": bytes,
                "extras": bytes,
            },
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "extensions": bytes,
    "extras": bytes,
    "images": [
        {
            "_type": flat.Image,
            "name": str,
            "uri": str,
            "mimeType": str,
            "bufferView": int,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "materials": [
        {
            "_type": flat.Material,
            "name": str,
            # "alphaMode": int,
            # "alphaCutoff": float,
            # "doubleSided": bool,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "meshes": [
        {
            "_type": flat.Mesh,
            "name": str,
            "primitives": [
                {
                    "_type": flat.MeshPrimitive,
                    "attributes": bytes,
                    "indices": int,
                    "material": int,
                    "mode": int,
                    "targets": bytes,
                    "extensions": bytes,
                    "extras": bytes,
                }
            ],
            "weights": [float],
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "nodes": [
        {
            "_type": flat.Node,
            "camera": int,
            "children": [int],
            "skin": int,
            "matrix": [float],
            "mesh": int,
            "rotation": [float],
            "scale": [float],
            "translation": [float],
            "weights": [float],
            "name": str,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "samplers": [
        {
            "_type": flat.Sampler,
            "name": str,
            "magFilter": int,
            "minFilter": int,
            "wrapS": (int, 10497),
            "wrapT": (int, 10497),
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "scenes": [
        {
            "_type": flat.Scene,
            "name": str,
            "nodes": [int],
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "skins": [
        {
            "_type": flat.Skin,
            "name": str,
            "inverseBindMatrices": int,
            "skeleton": int,
            "joints": [int],
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "textures": [
        {
            "_type": flat.Texture,
            "name": str,
            "sampler": int,
            "source": int,
            "extensions": bytes,
            "extras": bytes,
        }
    ],
    "scene": int,
}

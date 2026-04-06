"""
图片应用服务模块。

这是什么：
- 这是应用层对真实图片入口的统一封装。

做什么：
- 为上层提供“从引用、字节流、二进制、Base64 构建图片资产”的入口。
- 屏蔽底层图片读取和标准化细节。

为什么这么做：
- CLI、API 和测试都需要图片入口，但不应该都直接操作基础设施层细节。
- 把图片入口收口到应用层后，后续替换对象存储 SDK 或新增图片预处理都会更容易。
"""

from __future__ import annotations

from io import BufferedIOBase

from app.domain.models import InputAsset
from app.infrastructure.media.image_loader import (
    DEFAULT_IMAGE_PROMPT,
    build_image_asset,
    build_image_asset_from_reference,
    load_image_from_base64,
    load_image_from_bytes,
    load_image_from_stream,
)


def create_image_asset_from_reference(reference: str) -> tuple[str, InputAsset]:
    """
    从字符串引用创建图片资产。

    这是什么：
    - 这是上层最常用的真实图片入口。

    做什么：
    - 自动识别本地路径、HTTP/HTTPS URL 和对象存储 URI。
    - 返回默认分析提示词和标准化后的图片资产。

    为什么这么做：
    - 上层只需要表达“我要分析这张图”，不需要关心底层到底怎么读取。
    """
    return build_image_asset_from_reference(reference)


def create_image_asset_from_binary(data: bytes, *, name: str = "image.bin") -> tuple[str, InputAsset]:
    """
    从二进制字节创建图片资产。

    这是什么：
    - 这是“二进制图片入口”的应用层包装。

    做什么：
    - 接收原始字节并生成图片资产。

    为什么这么做：
    - 很多对象存储 SDK、上传接口和消息队列最终都会给到字节内容。
    """
    return DEFAULT_IMAGE_PROMPT, build_image_asset(load_image_from_bytes(data, name=name, source="bytes"))


def create_image_asset_from_bytes(data: bytes, *, name: str = "image.bin") -> tuple[str, InputAsset]:
    """
    从字节创建图片资产。

    这是什么：
    - 这是 `create_image_asset_from_binary` 的同义入口。

    做什么：
    - 为更常见的 Python 术语“bytes”提供统一接口。

    为什么这么做：
    - 用户可能从“binary”或“bytes”任一角度理解这个能力，保留两个名字更直观。
    """
    return create_image_asset_from_binary(data, name=name)


def create_image_asset_from_base64(
    encoded_data: str,
    *,
    name: str = "image-base64.bin",
) -> tuple[str, InputAsset]:
    """
    从 Base64 创建图片资产。

    这是什么：
    - 这是 Base64 图片入口。

    做什么：
    - 解析 Base64，并生成标准化图片资产。

    为什么这么做：
    - 前端上传、消息中转和部分对象存储回调经常以 Base64 传图。
    """
    return DEFAULT_IMAGE_PROMPT, build_image_asset(
        load_image_from_base64(encoded_data, name=name, source="base64")
    )


def create_image_asset_from_stream(
    stream: BufferedIOBase,
    *,
    name: str = "image-stream.bin",
) -> tuple[str, InputAsset]:
    """
    从流创建图片资产。

    这是什么：
    - 这是流式图片入口。

    做什么：
    - 从文件流或内存流中读取图片，并生成标准化资产。

    为什么这么做：
    - Web 上传和对象存储下载流最常见的接口形式就是流。
    """
    return DEFAULT_IMAGE_PROMPT, build_image_asset(
        load_image_from_stream(stream, name=name, source="stream")
    )

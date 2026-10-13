import base64
from pathlib import Path

from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.components import At, AtAll, Image, Plain, Reply
from astrbot.core.platform.astr_message_event import AstrMessageEvent

from .avatar import AvatarManager


class MissingTargetError(Exception):
    """[patcher:meme-trigger] 用户没有显式提供 meme 所需的目标 / 参数。

    仅在 `require_explicit=True`（严格模式）下抛出，调用方应静默跳过。
    """


class ParamsCollector:
    """
    参数收集类
    """

    def __init__(self, config: AstrBotConfig, avatar_manager: AvatarManager):
        self.conf = config
        self.avatar_manager = avatar_manager

    async def _decode_image(self, src: str) -> bytes | None:
        """统一把 src 转成 bytes"""
        raw: bytes | None = None
        if Path(src).is_file():
            raw = Path(src).read_bytes()
        elif src.startswith("http"):
            raw = await self.avatar_manager.download_image(src)
        elif src.startswith("base64://"):
            return base64.b64decode(src[9:])
        return raw if isinstance(raw, bytes) else None

    async def get_extra(self, event: AstrMessageEvent, target_id: str):
        """从消息平台获取参数"""
        if event.get_platform_name() == "aiocqhttp":
            from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
                AiocqhttpMessageEvent,
            )

            assert isinstance(event, AiocqhttpMessageEvent)
            user_info = await event.bot.get_stranger_info(user_id=int(target_id))
            raw_nickname = user_info.get("nickname")
            nickname = str(raw_nickname if raw_nickname is not None else "Unknown")
            sex = user_info.get("sex")
            return nickname, sex
        # TODO 适配更多消息平台

    @staticmethod
    def _is_ignored_at(seg: At, event: AstrMessageEvent) -> bool:
        """[patcher:meme-trigger] 判断该 @ 段是否应被忽略。

        原始实现用「是否为消息链第一段」来排除 @bot，但本机已改为免 @bot 触发，
        `@某人 关键词` 这种写法会把真正的目标误丢。这里改为按真实身份排除：
        @bot 自身、@全体成员（AtAll.qq == "all"）、以及非数字 qq。
        """
        if isinstance(seg, AtAll):
            return True
        qq = str(getattr(seg, "qq", "") or "")
        if not qq.isdigit():
            return True
        return qq == str(event.get_self_id())

    async def _append_id_info(
        self,
        event: AstrMessageEvent,
        target_id: str,
        images: list,
        options: dict,
        name: str = "",
    ):
        """补齐昵称、性别、头像信息"""
        nickname = name or target_id
        try:
            if result := await self.get_extra(event, target_id):
                nickname, sex = result
                options["name"], options["gender"] = nickname, sex
        except Exception:
            # 目标 QQ 取不到资料（不存在 / 平台不支持）时降级，不打断整张 meme
            pass
        avatar = None
        if event.get_platform_name() in {"qq_official", "qq_official_webhook"}:
            appid = str(getattr(getattr(event.bot, "platform", None), "appid", ""))  # type: ignore
            avatar = await self.avatar_manager.get_qq_official_avatar(
                appid,
                target_id,
            )
        if not avatar:
            avatar = await self.avatar_manager.get_qq_avatar(target_id)
        if avatar:
            images.append((nickname, avatar))

    async def collect_params(self, event: AstrMessageEvent, params, require_explicit: bool = False):
        """收集参数，返回 (images, texts, options)。

        [patcher:meme-trigger] `require_explicit=True` 时为严格模式：
        用户必须显式给出 meme 所需的目标 / 参数（@某人、@QQ号、直接附图、引用里的图或文字），
        否则抛 `MissingTargetError`，由调用方静默跳过。
        不再自动回退到「发送者头像 → bot 头像 → default_texts」。
        """
        images: list[tuple[str, bytes]] = []
        texts: list[str] = []
        options: dict[str, bool | str | int | float] = {}
        explicit_images = 0
        explicit_texts = 0

        chain = event.get_messages()
        send_id: str = event.get_sender_id()
        self_id: str = event.get_self_id()
        sender_name: str = str(event.get_sender_name())

        async def _process_segment(seg, name: str):
            nonlocal explicit_images, explicit_texts
            if isinstance(seg, Image):
                if src := seg.url or seg.file:
                    if image := await self._decode_image(src):
                        images.append((name, image))
                        explicit_images += 1
            elif isinstance(seg, At):
                if self._is_ignored_at(seg, event):
                    return
                before = len(images)
                await self._append_id_info(
                    event,
                    str(seg.qq),
                    images,
                    options,
                    seg.name or name,
                )
                if len(images) > before:
                    explicit_images += 1
            elif isinstance(seg, Plain):
                plains: list[str] = seg.text.strip().split(" ")
                if len(plains) > 1:
                    for text in plains[1:]:
                        if text in {"左", "右", "上", "下"}:
                            # 解析方向参数
                            options["direction"] = {
                                "左": "left",
                                "右": "right",
                                "上": "top",
                                "下": "bottom",
                            }[text]
                            continue
                        # 解析其他参数
                        if "=" in text:
                            k, v = text.split("=", 1)
                            options[k] = v
                        #  解析@qq
                        elif text.startswith("@"):
                            target_id = text[1:]
                            before = len(images)
                            await self._append_id_info(
                                event, target_id, images, options
                            )
                            if len(images) > before:
                                explicit_images += 1
                        elif text.startswith("<@") and text.endswith(">"):
                            target_id = text[2:-1]
                            before = len(images)
                            await self._append_id_info(
                                event, target_id, images, options
                            )
                            if len(images) > before:
                                explicit_images += 1
                        elif text:
                            texts.append(text)
                            explicit_texts += 1

        reply_seg = next((seg for seg in chain if isinstance(seg, Reply)), None)
        if reply_seg and reply_seg.chain:
            name = str(reply_seg.sender_nickname or reply_seg.sender_id)
            for seg in reply_seg.chain:
                await _process_segment(seg, name)
        for seg in chain:
            await _process_segment(seg, sender_name)

        # [patcher:meme-trigger] 严格模式：只接受用户显式给出的目标 / 参数，
        # 在此处（自动兜底之前）判定，兜底逻辑对严格模式不生效。
        if require_explicit:
            need_images = int(getattr(params, "min_images", 0) or 0)
            need_texts = int(getattr(params, "min_texts", 0) or 0)
            if explicit_images < need_images or explicit_texts < need_texts:
                raise MissingTargetError(
                    "缺少显式目标/参数："
                    f"图片 {explicit_images}/{need_images}，文字 {explicit_texts}/{need_texts}"
                )

        # 确保图片数量在min_images到max_images之间(参数足够即可)
        if len(images) < params.min_images:
            image_count = len(images)
            await self._append_id_info(event, send_id, images, options, sender_name)
            if len(images) > image_count:
                images.insert(0, images.pop())
        if len(images) < params.min_images:
            if bot_avatar := await self.avatar_manager.get_qq_avatar(self_id):
                images.insert(0, ("bot", bot_avatar))
        images = images[: params.max_images]

        # 确保文本数量在min_texts到max_texts之间(参数足够即可)
        if len(texts) < params.min_texts and params.default_texts:
            texts.extend(params.default_texts)
        texts = texts[: params.max_texts]

        return images, texts, options

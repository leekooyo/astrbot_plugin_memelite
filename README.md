<div align="center">

# astrbot_plugin_memelite

_✨ [AstrBot](https://github.com/AstrBotDevs/AstrBot) 表情包制作插件 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
</div>

> 本仓库由 leekooyo 独立维护，基于 [Zhalslar 原项目](https://github.com/Zhalslar/astrbot_plugin_memelite)。请通过 AstrBot 的「仓库地址安装」使用 `https://github.com/leekooyo/astrbot_plugin_memelite`；原始基线与维护差异见 [UPSTREAM.md](UPSTREAM.md)。

**当前版本：v3.1.0。** 版本号以 [metadata.yaml](metadata.yaml) 为准。

## 💡 介绍

- 本插件负责处理聊天机器人与[表情包生成器 meme-generator](https://github.com/MeetWq/meme-generator) 的对接。
- 本插件调用当前 AstrBot 环境中安装的 meme-generator，具体可用表情取决于依赖版本和已下载资源。
- 增强功能：图片过大自动压缩、表情生成超时控制、表情黑名单、参数解析、支持 @用户 / @QQ 号、支持额外参数传递
- 代码包含对不同 meme-generator 版本接口的适配；实际兼容性以当前依赖安装结果为准。

## 📦 安装

在 AstrBot 中选择「通过仓库地址安装」，填写 `https://github.com/leekooyo/astrbot_plugin_memelite`。当前 `requirements.txt` 指定 `meme_generator~=0.2.0`；插件的 Python 依赖按 AstrBot 的安装流程处理。首次启动若需下载资源，请等待日志确认完成。

如果依赖安装或资源下载失败，请先查看 AstrBot 与插件日志，再按实际系统和报错补齐依赖。不要直接改动正在运行环境中的依赖版本；升级前备份插件配置与本机资源。

## ⚙️ 配置

请在 AstrBot 面板配置，插件管理 -> astrbot_plugin_memelite -> 操作 -> 插件配置

| 配置项              | 描述               | 默认值    |
|---------------------|------------------|---------|
| `need_prefix`       | 启用触发前缀，需要前缀或 @bot 才能触发 meme | `true` |
| `require_target`    | 生成表情时要求明确给出目标，避免误用聊天中的头像 | `true` |
| `extra_prefix`      | 额外前缀，填写后需附加该前缀才能触发，留空不启用 | `""` |
| `fuzzy_match`       | 模糊匹配触发，消息中含关键词即可触发，易误触 | `false` |
| `is_compress_image` | 压缩图片，限制生成图长宽不超过 512px 防刷屏 | `true` |
| `is_check_resources`| 启动时检查资源，缺失资源会自动下载，关闭可优化启动性能 | `true` |
| `meme_timeout`      | meme 生成超时时长，单位秒 | `15` |
| `memes_disabled_list`| meme 黑名单，屏蔽其中关键词的触发 | `[]` |

将 `need_prefix` 设为 `false` 后，可以直接发送「关键词 目标/参数」；插件只匹配消息开头的表情关键词，并避开其他插件已注册的顶层指令名。`require_target` 默认开启：需要图片或文字参数的表情必须明确给出目标或参数，不会自动借用发送者或机器人头像。

## ⌨️ 命令

| 命令 | 说明 |
| --- | --- |
| `<关键词> [参数]` | 触发表情合成；是否需要前缀取决于配置 |
| `/meme列表`（别名 `/meme帮助`） | 查看当前可用的表情关键词 |
| `/meme详情 <名称>` | 查看指定表情的参数 |
| `/禁用meme <名称>` | 禁用指定表情 |
| `/启用meme <名称>` | 启用指定表情 |
| `/meme黑名单` | 查看已禁用的表情 |

可用关键词随已安装的 meme-generator 资源变化。发送 `/meme列表` 查看当前环境的列表；使用 `/meme详情 <名称>` 查询参数。

## 🐔 使用说明

- 本插件支持从原始消息中提取参数，请用空格隔开参数，如 “喜报 nmsl”；
- 本插件支持从引用消息中提取参数，如“[引用的消息] 喜报”；
- 本插件支持获取任意 QQ 号的头像作为参数，如“踩 @<QQ号>”；
- 实际可用功能取决于平台是否提供图片与用户头像接口；QQ 特有的头像和提及行为需相应适配器。
- 只有将 `require_target` 关闭后，插件才会尝试用发送者、被 @ 的用户或机器人头像补足缺少的参数。

## 额外表情资源

额外表情及字体由 meme-generator 管理；安装方式和资源目录会随其版本及部署环境变化。需要扩展资源时请按 [meme-generator 项目文档](https://github.com/MeetWq/meme-generator) 操作，更新前备份本机资源与配置。

## 📌 注意事项

- 如果遇到中文字体显示为乱码，请按照[表情包生成器 meme-generator](https://github.com/MeetWq/meme-generator) 的文档安装缺失的字体。

- 此维护版的问题请在本仓库提交 Issue；运行时下载的资源、生成图片和 AstrBot 配置文件不要提交到仓库。

## 反馈与维护

此维护版的问题和改进请在本仓库提交 Issue 或 Pull Request；原项目与第三方表情资源的归属保持不变。

## 🔗 相关链接

- [meme-generator](https://github.com/MemeCrafters/meme-generator) - 表情包生成器
- [meme-generator Rust 重构版](https://github.com/MemeCrafters/meme-generator-rs) - 表情包生成器的 Rust 重构版
- [meme-generator 额外表情仓库](https://github.com/MemeCrafters/meme-generator-contrib)
- [meme-generator-rs 额外表情仓库](https://github.com/MemeCrafters/meme-generator-contrib-rs)
- [nonebot-plugin-memes](https://github.com/MemeCrafters/nonebot-plugin-memes) - 表情包生成器 meme-generator 的 Nonebot2 对接插件
- [AstrBot](https://astrbot.app/) - 易于上手的多平台聊天机器人及开发框架。

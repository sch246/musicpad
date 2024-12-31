# Music Pad

一个简单的音频播放器，支持多轨道播放、快捷键控制和多种播放模式。

建议配合 VoiceMetter 使用 （

![image.png](https://s2.loli.net/2025/01/01/jR4FAnauvDxO5Zw.png)

## 功能特点

- 支持多种音频格式 (mp3, wav, ogg, flac)
- 多轨道同时播放
- 全局快捷键控制
- 多种播放模式（重叠、单点、暂停、终止）
- 音量控制
- 循环播放
- 拖放支持
- 设置保存/加载

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/sch246/musicpad.git
cd musicpad
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用说明

在目录下运行：

```bash
python ./musicpad.py
```

### 播放模式

- 重叠模式：每次点击从头播放，不终止之前的播放
- 单点模式：每次点击从头播放
- 暂停模式：停止播放时暂停内容
- 终止模式：停止播放时终止内容（默认选择）

### 快捷操作

- 可以拖入音频文件
- tab 和 shift+tab：切换选择
- 上下方向键：移动音轨
- Delete：删除音轨
- Enter：播放/停止
- 左键方块：播放/暂停/继续
- 右键方块：停止
- 双击名称：选择音频
- Space：展开/折叠

## 许可证

本项目采用 GNU General Public License v3.0 许可证。详情请见 [LICENSE](LICENSE) 文件。

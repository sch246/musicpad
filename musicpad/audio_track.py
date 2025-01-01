
OVERLAP = "重叠模式"
SINGLE = "单点模式"
PAUSE = "暂停模式"
STOP = "终止模式"

import pygame
from pathlib import Path
from pygame.mixer import Channel

class AudioTrack:
    def __init__(self):
        self.sound = None
        self.channels: list[Channel] = []
        self.volume = 0
        self.is_playing = False
        self.is_paused = False
        self.loop = False
        self.mode = STOP
        self.path = ""

    def load_file(self, file_path:str):
        """加载音频文件"""
        if not file_path or not Path(file_path).exists():
            self.sound = None
            self.path = ""
            return False

        try:
            self.sound = pygame.mixer.Sound(file_path)
            self.path = file_path
            self.set_volume(self.volume*100)
            return True
        except Exception as e:
            print(f"加载音频文件失败: {e}")
            self.sound = None
            self.path = ""
            return False

    def toggle_play(self, is_hold_mode: bool, is_key_down: bool):
        """按状态播放音频"""
        if not self.sound:
            return

        # 切换触发： 按下 True 松开 按下 True 松开 按下 True ...
        # 按住触发: 按下 True 松开 False 按下 True ...
        # print('play', is_key_down)
        should_start = is_key_down if is_hold_mode else not self.is_active()
        self.cleanup_channels()

        if self.mode == OVERLAP:
            # 重叠模式：直接播放新实例
            if is_key_down:
                self.play()

        elif self.mode == SINGLE:
            # 单点模式：停止当前播放并重新开始
            if is_key_down:
                self.stop()
                self.play()

        elif self.mode == PAUSE:
            if should_start:
                if not self.is_playing:
                    # 新开始播放
                    self.play()
                elif self.is_paused:
                    # 继续播放
                    self.unpause()
            else:
                if self.is_playing:
                    # 暂停播放
                    self.pause()

        elif self.mode == STOP:
            # 终止模式：停止当前播放并重新开始
            self.stop()
            if should_start:
                self.play()

    def toggle_stop(self):
        '''播放/停止'''
        if not self.sound:
            return
        self.cleanup_channels()
        if self.is_active():
            self.stop()
        else:
            if self.is_paused:
                self.stop()
            self.play()

    def toggle_pause(self):
        '''播放/暂停/继续'''
        if not self.sound:
            return
        if not self.is_active():
            if not self.is_playing:
                # 新开始播放
                self.play()
            elif self.is_paused:
                # 继续播放
                self.unpause()
        else:
            if self.is_playing:
                # 暂停播放
                self.pause()

    def play(self):
        channel = self.sound.play(loops=-1 if self.loop else 0)
        self.channels.append(channel)
        self.is_playing = True
        self.is_paused = False

    def stop(self):
        """停止播放"""
        if self.sound:
            self.sound.stop()
        self.channels.clear()
        self.is_playing = False
        self.is_paused = False

    def pause(self):
        '''暂停播放'''
        for channel in self.channels:
            channel.pause()
        self.is_paused = True

    def unpause(self):
        '''继续播放'''
        for channel in self.channels:
            channel.unpause()
        self.is_paused = False
        self.is_playing = True

    def set_volume(self, db):
        """设置音量 (db)"""
        self.volume = max(-60, min(0, db))  # 限制在 -60dB 到 0dB 之间
        self.volume = pow(10, self.volume / 20.0)
        if self.sound:
            self.sound.set_volume(self.volume)

    def is_active(self):
        """检查是否正在播放"""
        return self.is_playing and not self.is_paused

    def cleanup_channels(self):
        """清理未在播放的通道"""
        self.channels = [ch for ch in self.channels
            if ch.get_busy() and ch.get_sound() is self.sound]

        if not self.channels:
            self.is_playing = False
            self.is_paused = False

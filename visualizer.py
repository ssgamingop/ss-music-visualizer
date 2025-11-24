import pyaudio
import numpy as np
import pygame
import os
import wave
import math
import random
from scipy.fftpack import fft

# basic settings
INITIAL_WIDTH = 1200
INITIAL_HEIGHT = 800
FPS = 60

# colors define
COLOR_BG = (5, 5, 10)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (100, 100, 100)
COLOR_ACCENT = (0, 255, 200)

CHUNK = 2048 

class MusicVisualizer:
    def __init__(self):
        pygame.init()
        self.width = INITIAL_WIDTH
        self.height = INITIAL_HEIGHT
        # window resizeable
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("SS Music Visualizer")
        self.clock = pygame.time.Clock()
        
        # fonts setup
        self.font = pygame.font.SysFont("Segoe UI", 16)
        self.font_title = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_time = pygame.font.SysFont("Consolas", 14)
        self.font_hud = pygame.font.SysFont("Arial", 40, bold=True)

        # audio setup
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.wf = None
        self.is_playing = False
        self.current_song_index = -1
        
        # song details
        self.total_frames = 0
        self.current_frame_pos = 0
        self.frame_rate = 44100
        
        # controls vars
        self.sensitivity = 30
        self.viz_mode = 0 # 0 bars, 1 circle
        self.hud_timer = 0
        self.hud_text = ""
        self.is_dragging_seek = False 
        
        # songs folder check
        self.songs_dir = "songs"
        self.playlist = self.load_songs()
        
        # maths for visualizer
        self.num_bars = 90 
        self.bar_heights = np.zeros(self.num_bars)
        self.window = np.hanning(CHUNK) 
        
        # particles list
        self.particles = []
        self.hue_offset = 0
        self.glow_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def load_songs(self):
        # folder nahi hai to bana do
        if not os.path.exists(self.songs_dir): os.makedirs(self.songs_dir); return []
        return sorted([f for f in os.listdir(self.songs_dir) if f.endswith(".wav")])

    def clean_name(self, filename):
        # removing .wav and underscores
        return os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()

    def show_hud(self, text):
        self.hud_text = text
        self.hud_timer = 60

    def play_song(self, index):
        if index < 0 or index >= len(self.playlist): return
        
        # old stream off
        if self.stream: self.stream.stop_stream(); self.stream.close()
        if self.wf: self.wf.close()

        path = os.path.join(self.songs_dir, self.playlist[index])
        try:
            self.wf = wave.open(path, 'rb')
        except: return

        self.total_frames = self.wf.getnframes()
        self.frame_rate = self.wf.getframerate()
        self.current_frame_pos = 0

        # new stream start
        self.stream = self.p.open(format=self.p.get_format_from_width(self.wf.getsampwidth()),
                                  channels=self.wf.getnchannels(),
                                  rate=self.frame_rate,
                                  output=True)
        self.is_playing = True
        self.current_song_index = index

    def seek_to(self, x_pos):
        # seek logic using mouse pos
        if not self.wf or self.total_frames == 0: return
        
        bar_x = 20
        bar_width = 210
        
        rel_x = x_pos - bar_x
        pct = max(0.0, min(1.0, rel_x / bar_width))
        
        target_frame = int(pct * self.total_frames)
        
        try:
            self.wf.setpos(target_frame)
            self.current_frame_pos = target_frame
        except wave.Error:
            pass

    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02}:{s:02}"

    def process_audio(self):
        # audio read 
        if self.is_playing and self.wf and not self.is_dragging_seek:
            data = self.wf.readframes(CHUNK)
            if len(data) < CHUNK * self.wf.getsampwidth():
                self.wf.rewind()
                data = self.wf.readframes(CHUNK)
                self.current_frame_pos = 0
            
            self.stream.write(data)
            self.current_frame_pos += CHUNK
            
            indata = np.frombuffer(data, dtype=np.int16)
            if self.wf.getnchannels() == 2:
                indata = indata.reshape(-1, 2).mean(axis=1)
            return indata
        return np.zeros(CHUNK)

    def get_rainbow_color(self, i, total):
        hue = (self.hue_offset + (i / total) * 180) % 360
        c = pygame.Color(0)
        c.hsla = (hue, 100, 50, 100)
        return c

    def draw_neon_rect(self, surf, color, rect, border_radius=0):
        # glow effect ke liye transparent rect
        glow_color = (color.r, color.g, color.b, 50) 
        pygame.draw.rect(surf, glow_color, rect, border_radius=border_radius)
        # main bright core
        core_color = (min(255, color.r + 100), min(255, color.g + 100), min(255, color.b + 100), 255)
        core_rect = (rect[0]+1, rect[1]+1, max(1, rect[2]-2), max(1, rect[3]-2))
        pygame.draw.rect(surf, core_color, core_rect, border_radius=border_radius)

    def draw_neon_line(self, surf, color, start, end, width):
        glow_color = (color.r, color.g, color.b, 60)
        pygame.draw.line(surf, glow_color, start, end, width + 4)
        core_color = (min(255, color.r + 80), min(255, color.g + 80), min(255, color.b + 80), 255)
        pygame.draw.line(surf, core_color, start, end, width)

    def draw_particles(self, center_x, center_y, beat_intensity):
        # particles spawn when bass is heavy
        if beat_intensity > 50: 
            for _ in range(3): 
                angle = random.uniform(0, 6.28)
                speed = random.uniform(2, 8)
                c = self.get_rainbow_color(random.randint(0, 100), 100)
                self.particles.append({
                    'x': center_x, 'y': center_y,
                    'dx': math.cos(angle) * speed, 'dy': math.sin(angle) * speed,
                    'life': 255, 'color': c, 'size': random.randint(2, 5)
                })

        # move particles
        for p in self.particles[:]:
            p['x'] += p['dx']
            p['y'] += p['dy']
            p['life'] -= 4
            if p['life'] <= 0:
                self.particles.remove(p)
                continue
            
            pygame.draw.circle(self.glow_surface, (p['color'].r, p['color'].g, p['color'].b, max(0, p['life']//4)), 
                             (int(p['x']), int(p['y'])), p['size'] * 2)
            pygame.draw.circle(self.glow_surface, (255, 255, 255, p['life']), 
                             (int(p['x']), int(p['y'])), p['size'])

    def draw_visualizer(self, raw_data):
        if len(raw_data) < CHUNK: return
        
        self.glow_surface.fill((0,0,0,0))
        self.hue_offset = (self.hue_offset + 0.5) % 360
        
        # fft calculation
        windowed = raw_data * self.window
        fft_complex = fft(windowed)
        fft_mag = np.abs(fft_complex)[:CHUNK//2]
        fft_mag = fft_mag[5:] 
        fft_mag = np.log10(fft_mag + 1)

        step = len(fft_mag) // self.num_bars
        target_heights = []
        for i in range(self.num_bars):
            val = np.mean(fft_mag[i*step : (i+1)*step])
            target_heights.append(val * self.sensitivity)

        bass_energy = np.mean(target_heights[:10]) 

        viz_width = self.width - 250
        center_x = 250 + (viz_width // 2)
        center_y = self.height // 2
        
        # screen shake effect
        if bass_energy > 60:
            center_x += random.randint(-3, 3)
            center_y += random.randint(-3, 3)

        self.draw_particles(center_x, center_y, bass_energy)

        if self.viz_mode == 0:
            # dabba mode
            display_bars = self.num_bars // 2
            bar_width = (viz_width // (display_bars * 2)) - 2
            if bar_width < 2: bar_width = 2
            
            for i in range(display_bars):
                idx = i * 2
                if idx >= len(target_heights): break

                # smooth height transition
                self.bar_heights[i] += (target_heights[idx] - self.bar_heights[i]) * 0.2
                h = min(self.bar_heights[i], self.height // 2 - 20)
                
                color = self.get_rainbow_color(i, display_bars)
                
                x_right = center_x + 5 + i * (bar_width + 2)
                rect_r = (x_right, center_y - h, bar_width, h)
                self.draw_neon_rect(self.glow_surface, color, rect_r, 3)
                
                # reflection
                rect_r_ref = (x_right, center_y, bar_width, h * 0.7) 
                pygame.draw.rect(self.glow_surface, (color.r, color.g, color.b, 60), rect_r_ref, border_radius=3)

                x_left = center_x - 5 - (i + 1) * (bar_width + 2)
                rect_l = (x_left, center_y - h, bar_width, h)
                self.draw_neon_rect(self.glow_surface, color, rect_l, 3)
                
                rect_l_ref = (x_left, center_y, bar_width, h * 0.7)
                pygame.draw.rect(self.glow_surface, (color.r, color.g, color.b, 60), rect_l_ref, border_radius=3)
        
        else:
            # goola mode
            radius = 100
            if bass_energy > 40: radius += 5
            
            orb_color = self.get_rainbow_color(0, 10)
            pygame.draw.circle(self.glow_surface, (orb_color.r, orb_color.g, orb_color.b, 50), (center_x, center_y), radius)
            pygame.draw.circle(self.glow_surface, (255, 255, 255, 255), (center_x, center_y), radius - 5, 2)
            
            circle_data = list(reversed(target_heights)) + target_heights
            total_points = len(circle_data)
            
            for i in range(total_points):
                idx = i if i < self.num_bars else total_points - 1 - i
                self.bar_heights[idx] += (circle_data[i] - self.bar_heights[idx]) * 0.2
                h = min(self.bar_heights[idx] * 0.8, 300)
                
                angle = (i / total_points) * 2 * math.pi - (math.pi / 2)
                start_x = center_x + radius * math.cos(angle)
                start_y = center_y + radius * math.sin(angle)
                end_x = center_x + (radius + h) * math.cos(angle)
                end_y = center_y + (radius + h) * math.sin(angle)
                
                color = self.get_rainbow_color(i, total_points)
                self.draw_neon_line(self.glow_surface, color, (start_x, start_y), (end_x, end_y), 4)

        self.screen.blit(self.glow_surface, (0,0))

    def draw_ui(self):
        # sidebar draw
        pygame.draw.rect(self.screen, (20, 20, 25), (0, 0, 250, self.height))
        pygame.draw.line(self.screen, (50, 50, 60), (250, 0), (250, self.height))

        # progress bar stuff
        if self.is_playing and self.total_frames > 0:
            if self.is_dragging_seek:
                mx = pygame.mouse.get_pos()[0]
                pct = max(0.0, min(1.0, (mx - 20) / 210))
            else:
                pct = self.current_frame_pos / self.total_frames
            
            cur_sec = (pct * self.total_frames) / self.frame_rate
            tot_sec = self.total_frames / self.frame_rate
            time_str = f"{self.format_time(cur_sec)} / {self.format_time(tot_sec)}"
            
            t_surf = self.font_time.render(time_str, True, COLOR_ACCENT)
            self.screen.blit(t_surf, (20, self.height - 60))
            
            bar_rect = (20, self.height - 35, 210, 8) 
            pygame.draw.rect(self.screen, (50,50,50), bar_rect, border_radius=4)
            
            fill_rect = (20, self.height - 35, int(210 * pct), 8)
            pygame.draw.rect(self.screen, COLOR_ACCENT, fill_rect, border_radius=4)
            
            handle_x = 20 + int(210 * pct)
            pygame.draw.circle(self.screen, (255, 255, 255), (handle_x, self.height - 31), 6)

        # playlist rendering
        self.screen.blit(self.font_title.render("Sa Re Ga...", True, COLOR_TEXT), (20, 20))
        for i, song in enumerate(self.playlist):
            y_pos = 70 + i * 30
            if y_pos > self.height - 100: break
            
            col = COLOR_ACCENT if i == self.current_song_index else COLOR_TEXT_DIM
            if i == self.current_song_index:
                 pygame.draw.rect(self.screen, (30, 60, 60), (10, y_pos-5, 230, 28), border_radius=5)
            
            name = self.clean_name(song)[:22]
            self.screen.blit(self.font.render(f"{i+1}. {name}", True, col), (20, y_pos))

        info = self.font.render("M: Mode | UP/DWN: Size", True, (80, 80, 100))
        self.screen.blit(info, (20, self.height - 20))

        # hud
        if self.hud_timer > 0:
            self.hud_timer -= 1
            surf = self.font_hud.render(self.hud_text, True, COLOR_TEXT)
            rect = surf.get_rect(center=(self.width//2 + 125, self.height//2))
            bg = pygame.Surface((rect.width + 40, rect.height + 20))
            bg.fill((0,0,0)); bg.set_alpha(150)
            self.screen.blit(bg, (rect.x-20, rect.y-10))
            self.screen.blit(surf, rect)

    def run(self):
        running = True
        while running:
            self.screen.fill(COLOR_BG)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.glow_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

                # mouse inputs
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if event.button == 1: # left click
                        # playlist click logic
                        if mx < 250 and my < self.height - 70:
                            idx = (my - 70) // 30
                            if 0 <= idx < len(self.playlist): self.play_song(idx)
                        
                        # seek bar click logic
                        if 10 < mx < 240 and self.height - 50 < my < self.height - 20:
                            self.is_dragging_seek = True
                            self.seek_to(mx)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        if self.is_dragging_seek:
                            self.seek_to(pygame.mouse.get_pos()[0])
                            self.is_dragging_seek = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: self.is_playing = not self.is_playing
                    if event.key == pygame.K_m:
                        self.viz_mode = 1 - self.viz_mode 
                        self.show_hud("GOOLA" if self.viz_mode else "DABBA")
                    if event.key == pygame.K_UP:
                        self.sensitivity += 2; self.show_hud(f"SIZE: {self.sensitivity}")
                    if event.key == pygame.K_DOWN:
                        self.sensitivity = max(2, self.sensitivity - 2); self.show_hud(f"SIZE: {self.sensitivity}")
                    if event.key == pygame.K_F11:
                         if self.screen.get_flags() & pygame.FULLSCREEN:
                            pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
                         else:
                            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

            raw = self.process_audio()
            self.draw_visualizer(raw)
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(FPS)

        if self.stream: self.stream.stop_stream(); self.stream.close()
        if self.wf: self.wf.close()
        self.p.terminate()
        pygame.quit()

if __name__ == "__main__":
    MusicVisualizer().run()
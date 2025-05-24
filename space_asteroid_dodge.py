import pygame
import random
import sys
import math
import os

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_X_MIN = 50
PLAYER_X_MAX = SCREEN_WIDTH - 50

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
DARK_BLUE = (0, 0, 50)
LIGHT_BLUE = (100, 100, 255)
SILVER = (192, 192, 192)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
PURPLE = (128, 0, 128)

# Game variables
score = 0
game_speed = 5
game_over = False
win_score = 1000
high_score = 0

# Create a nebula effect for background
nebula = []
for _ in range(20):
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, SCREEN_HEIGHT)
    size = random.randint(100, 300)
    color_choice = random.choice([(PURPLE[0]//4, 0, PURPLE[2]//4), (0, 0, BLUE[2]//3)])
    nebula.append([x, y, size, color_choice])

# Stars for background
stars = []
for _ in range(300):  # More stars
    x = random.randint(0, SCREEN_WIDTH)
    y = random.randint(0, SCREEN_HEIGHT)
    size = random.randint(1, 3)
    brightness = random.randint(100, 255)
    stars.append([x, y, size, brightness])

class SpaceObject:
    def __init__(self, x, y, width, height, color, speed):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.speed = speed
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
    
    def update(self):
        self.y += self.speed
        self.rect.center = (self.x, self.y)
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

class Astronaut(SpaceObject):
    def __init__(self):
        super().__init__(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, 50, 70, WHITE, 0)
        self.flame_size = 0
        self.shield_active = False
        self.shield_timer = 0
        self.shield_radius = 60
        self.animation_frame = 0
        self.animation_speed = 0.2
        self.thruster_particles = []
        self.exploding = False
        self.explosion_start_time = 0
        self.explosion_duration = 1000  # 1 second in milliseconds
    
    def move_left(self):
        self.x = max(PLAYER_X_MIN, self.x - 20)
    
    def move_right(self):
        self.x = min(PLAYER_X_MAX, self.x + 20)
    
    def activate_shield(self):
        if not self.shield_active:
            self.shield_active = True
            self.shield_timer = 180  # 3 seconds at 60 FPS
    
    def update(self):
        self.rect.center = (self.x, self.y)
        self.flame_size = (self.flame_size + 1) % 10
        self.animation_frame = (self.animation_frame + self.animation_speed) % 4
        
        # Update shield
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False
        
        # Update thruster particles
        for particle in self.thruster_particles[:]:
            particle[0] += particle[2]  # x position
            particle[1] += particle[3]  # y position
            particle[4] -= 0.5  # lifetime
            if particle[4] <= 0:
                self.thruster_particles.remove(particle)
        
        # Add new thruster particles
        if random.random() < 0.4:
            self.thruster_particles.append([
                self.x + random.uniform(-10, 10),
                self.y + self.height // 2 + random.uniform(0, 10),
                random.uniform(-0.5, 0.5),
                random.uniform(2, 4),
                random.uniform(5, 10),
                (255, random.randint(100, 200), 0)
            ])
    
    def draw(self, screen):
        # If exploding, don't draw the normal astronaut
        if self.exploding:
            # Check if we should still show the explosion or if it's time for game over
            current_time = pygame.time.get_ticks()
            explosion_elapsed = current_time - self.explosion_start_time
            
            # Draw explosion effect based on time elapsed
            if explosion_elapsed < self.explosion_duration:
                # Draw fragmented parts of the ship
                explosion_progress = explosion_elapsed / self.explosion_duration
                
                # Draw disintegrating ship parts
                for i in range(10):
                    # Calculate fragment positions with increasing spread over time
                    spread = explosion_progress * 30
                    fragment_x = self.x + random.uniform(-spread, spread)
                    fragment_y = self.y + random.uniform(-spread, spread)
                    fragment_size = random.randint(3, 8)
                    
                    # Determine fragment color (parts of the ship)
                    if i % 3 == 0:
                        color = SILVER  # Ship body
                    elif i % 3 == 1:
                        color = LIGHT_BLUE  # Cockpit
                    else:
                        color = GRAY  # Wings
                    
                    # Draw the fragment
                    pygame.draw.rect(screen, color, 
                                    (fragment_x, fragment_y, fragment_size, fragment_size))
                
                # Draw fire at the center of explosion
                fire_size = 40 - int(explosion_progress * 20)
                if fire_size > 0:
                    pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), fire_size)
                    pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), fire_size // 2)
            
            return  # Skip drawing the normal astronaut
        
        # Draw thruster particles
        for particle in self.thruster_particles:
            # Create a surface for the glow
            glow_size = int(particle[4] * 2)
            glow_surf = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
            
            # Draw gradient glow
            for radius in range(glow_size, 0, -1):
                alpha = 150 * (radius / glow_size)
                color = (particle[5][0], particle[5][1], 0, alpha)
                pygame.draw.circle(glow_surf, color, (glow_size, glow_size), radius)
            
            # Blit the glow
            screen.blit(glow_surf, (particle[0] - glow_size, particle[1] - glow_size))
        
        # Draw main rocket flames
        flame_height = 25 + self.flame_size
        flame_width_base = 20
        flame_points = [
            (self.x - flame_width_base//2, self.y + self.height // 2),
            (self.x, self.y + self.height // 2 + flame_height),
            (self.x + flame_width_base//2, self.y + self.height // 2)
        ]
        
        # Create a surface for the flame glow
        glow_surf = pygame.Surface((flame_width_base + 30, flame_height + 30), pygame.SRCALPHA)
        
        # Draw gradient flame glow
        flame_center = (flame_width_base//2 + 15, 15)
        for radius in range(flame_height, 0, -5):
            alpha = 100 * (radius / flame_height)
            color = (255, 150, 50, alpha)
            pygame.draw.circle(glow_surf, color, flame_center, radius)
        
        # Blit the flame glow
        screen.blit(glow_surf, (self.x - flame_width_base//2 - 15, self.y + self.height // 2 - 15))
        
        # Draw the actual flames
        pygame.draw.polygon(screen, ORANGE, flame_points)
        
        # Inner flame
        inner_flame_points = [
            (self.x - flame_width_base//4, self.y + self.height // 2 + 5),
            (self.x, self.y + self.height // 2 + flame_height - 10),
            (self.x + flame_width_base//4, self.y + self.height // 2 + 5)
        ]
        pygame.draw.polygon(screen, YELLOW, inner_flame_points)
        
        # Draw shield if active
        if self.shield_active:
            # Create pulsating effect
            pulse = math.sin(pygame.time.get_ticks() * 0.01) * 5 + self.shield_radius
            
            # Draw outer shield glow
            for radius in range(int(pulse) + 10, int(pulse) - 10, -2):
                if radius <= 0:
                    continue
                alpha = 10 + 40 * ((radius - (pulse - 10)) / 20)
                shield_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                shield_color = (100, 150, 255, alpha)
                pygame.draw.circle(shield_surf, shield_color, (radius, radius), radius)
                screen.blit(shield_surf, (self.x - radius, self.y - radius))
            
            # Draw shield hexagon pattern
            shield_surf = pygame.Surface((int(pulse)*2, int(pulse)*2), pygame.SRCALPHA)
            for i in range(0, 360, 60):  # Draw 6 segments
                angle1 = math.radians(i)
                angle2 = math.radians(i + 60)
                x1 = int(pulse + pulse * 0.9 * math.cos(angle1))
                y1 = int(pulse + pulse * 0.9 * math.sin(angle1))
                x2 = int(pulse + pulse * 0.9 * math.cos(angle2))
                y2 = int(pulse + pulse * 0.9 * math.sin(angle2))
                pygame.draw.line(shield_surf, (200, 220, 255, 100), (x1, y1), (x2, y2), 2)
            
            # Draw inner shield
            pygame.draw.circle(shield_surf, (100, 150, 255, 30), (int(pulse), int(pulse)), int(pulse * 0.7))
            
            screen.blit(shield_surf, (self.x - int(pulse), self.y - int(pulse)))
        
        # Draw astronaut body (Rafale jet-inspired design)
        # Main body
        body_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw sleek body shape
        body_points = [
            (5, 15),  # Top left
            (self.width - 5, 15),  # Top right
            (self.width - 2, self.height - 20),  # Bottom right
            (self.width//2 + 10, self.height),  # Bottom middle right
            (self.width//2, self.height - 5),  # Bottom middle
            (self.width//2 - 10, self.height),  # Bottom middle left
            (2, self.height - 20)  # Bottom left
        ]
        pygame.draw.polygon(body_surf, SILVER, body_points)
        
        # Add metallic shading
        highlight_points = [
            (8, 18),
            (self.width - 8, 18),
            (self.width - 5, self.height//2),
            (8, self.height//2)
        ]
        pygame.draw.polygon(body_surf, WHITE, highlight_points)
        
        # Add cockpit (helmet)
        cockpit_rect = pygame.Rect(self.width//2 - 12, 5, 24, 20)
        pygame.draw.ellipse(body_surf, LIGHT_BLUE, cockpit_rect)
        
        # Add cockpit reflection
        reflection_rect = pygame.Rect(self.width//2 - 8, 8, 6, 4)
        pygame.draw.ellipse(body_surf, WHITE, reflection_rect)
        
        # Add wing details
        wing_y = self.height - 30
        # Left wing
        pygame.draw.polygon(body_surf, GRAY, [
            (0, wing_y),
            (2, wing_y),
            (5, self.height - 15),
            (0, self.height - 20)
        ])
        # Right wing
        pygame.draw.polygon(body_surf, GRAY, [
            (self.width, wing_y),
            (self.width - 2, wing_y),
            (self.width - 5, self.height - 15),
            (self.width, self.height - 20)
        ])
        
        # Add engine details
        pygame.draw.rect(body_surf, DARK_BLUE, (self.width//2 - 8, self.height - 25, 16, 20), border_radius=3)
        pygame.draw.rect(body_surf, BLACK, (self.width//2 - 6, self.height - 15, 12, 10), border_radius=2)
        
        # Add decorative lines
        pygame.draw.line(body_surf, GRAY, (self.width//2, 25), (self.width//2, self.height - 25), 1)
        pygame.draw.line(body_surf, GRAY, (10, self.height//2), (self.width - 10, self.height//2), 1)
        
        # Add animated lights
        light_pos = int(self.animation_frame)
        pygame.draw.circle(body_surf, RED, (5, 30 + light_pos), 2)
        pygame.draw.circle(body_surf, GREEN, (self.width - 5, 30 + light_pos), 2)
        
        # Blit the astronaut body
        screen.blit(body_surf, (self.rect.left, self.rect.top))

# Define meteor colors
METEOR_COLORS = [
    (120, 90, 60),    # Dark brown
    (160, 110, 70),   # Medium brown
    (180, 130, 80),   # Light brown
    (100, 100, 100),  # Gray
    (70, 70, 80),     # Dark gray
    (130, 100, 70),   # Reddish brown
    (80, 70, 60)      # Very dark brown
]

class Asteroid(SpaceObject):
    def __init__(self, x, y):
        # Randomly choose between meteor types
        self.meteor_type = random.choice(["stony", "iron", "stony-iron"])
        size = random.randint(50, 100)  # Larger size for more detail
        
        # Set base color based on meteor type
        if self.meteor_type == "stony":
            base_color = random.choice(METEOR_COLORS[:3])  # Browns
        elif self.meteor_type == "iron":
            base_color = random.choice(METEOR_COLORS[3:5])  # Grays
        else:  # stony-iron
            base_color = random.choice(METEOR_COLORS[5:])  # Reddish browns
            
        super().__init__(x, y, size, size, base_color, game_speed)
        self.rotation = random.randint(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        self.points = []
        self.crater_positions = []
        self.color_variation = random.randint(-20, 20)
        self.texture_noise = []
        
        # Burning trail effect for entering atmosphere
        self.trail_particles = []
        self.trail_color = (255, random.randint(100, 200), 0, 150)  # Orange-red with alpha
        
        # Glowing effect for heated meteors
        self.glow_color = random.choice([
            (255, 100, 0, 40),  # Orange glow
            (255, 50, 0, 40),   # Red-orange glow
            (255, 200, 0, 30)   # Yellow-orange glow
        ])
        self.has_glow = random.random() < 0.4  # 40% chance of having a glow
        self.generate_shape()
    
    def generate_shape(self):
        # Shape varies by meteor type
        if self.meteor_type == "stony":
            # Stony meteors are more irregular with many bumps
            num_points = random.randint(14, 20)
            irregularity = 0.4  # Higher irregularity
        elif self.meteor_type == "iron":
            # Iron meteors are smoother with fewer points
            num_points = random.randint(8, 12)
            irregularity = 0.2  # Lower irregularity
        else:  # stony-iron
            # Mix of both characteristics
            num_points = random.randint(10, 16)
            irregularity = 0.3  # Medium irregularity
        
        self.points = []
        
        # Create base shape
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            # Variation based on meteor type
            distance = self.width // 2 * random.uniform(1.0 - irregularity, 1.0 + irregularity)
            x = int(math.cos(angle) * distance)
            y = int(math.sin(angle) * distance)
            self.points.append((x, y))
        
        # Add some smaller bumps for more realism (more for stony, fewer for iron)
        bump_chance = 0.4 if self.meteor_type == "stony" else 0.2 if self.meteor_type == "iron" else 0.3
        extra_points = []
        for i in range(0, len(self.points)-1):
            if random.random() < bump_chance:
                x1, y1 = self.points[i]
                x2, y2 = self.points[i+1]
                mid_x = (x1 + x2) // 2
                mid_y = (y1 + y2) // 2
                # Add random displacement
                bump_size = random.uniform(0.1, 0.3) * self.width // 2
                angle = math.atan2(y2 - y1, x2 - x1) + math.pi/2
                mid_x += int(math.cos(angle) * bump_size)
                mid_y += int(math.sin(angle) * bump_size)
                extra_points.append((i+1, (mid_x, mid_y)))
        
        # Insert the extra points
        offset = 0
        for idx, point in extra_points:
            self.points.insert(idx + offset, point)
            offset += 1
        
        # Pre-generate crater positions with more variety
        # Stony meteors have more craters, iron have fewer
        if self.meteor_type == "stony":
            num_craters = random.randint(5, 10)
        elif self.meteor_type == "iron":
            num_craters = random.randint(2, 5)
        else:  # stony-iron
            num_craters = random.randint(3, 7)
            
        self.crater_positions = []
        for _ in range(num_craters):
            crater_x = random.randint(-self.width//3, self.width//3)
            crater_y = random.randint(-self.height//3, self.height//3)
            crater_size = random.randint(5, 15)
            crater_depth = random.uniform(0.6, 1.0)  # Depth factor for 3D effect
            
            # Crater color based on meteor type
            if self.meteor_type == "stony":
                # Lighter craters for stony meteors
                crater_color = (
                    min(255, max(0, self.color[0] + random.randint(10, 30))),
                    min(255, max(0, self.color[1] + random.randint(10, 30))),
                    min(255, max(0, self.color[2] + random.randint(10, 30)))
                )
            elif self.meteor_type == "iron":
                # Darker, metallic craters for iron meteors
                crater_color = (
                    min(255, max(0, self.color[0] - random.randint(10, 30))),
                    min(255, max(0, self.color[1] - random.randint(10, 30))),
                    min(255, max(0, self.color[2] - random.randint(10, 30)))
                )
            else:  # stony-iron
                # Mixed coloration
                crater_color = (
                    min(255, max(0, self.color[0] + random.randint(-20, 20))),
                    min(255, max(0, self.color[1] + random.randint(-20, 20))),
                    min(255, max(0, self.color[2] + random.randint(-20, 20)))
                )
                
            self.crater_positions.append((crater_x, crater_y, crater_size, crater_color, crater_depth))
        
        # Generate texture noise for surface detail
        self.texture_noise = []
        
        # Different texture patterns based on meteor type
        if self.meteor_type == "stony":
            # More varied textures for stony meteors
            num_noise = random.randint(40, 60)
            noise_size_range = (1, 4)
        elif self.meteor_type == "iron":
            # Smoother with metallic streaks for iron meteors
            num_noise = random.randint(20, 35)
            noise_size_range = (1, 3)
        else:  # stony-iron
            # Mix of both
            num_noise = random.randint(30, 50)
            noise_size_range = (1, 4)
            
        for _ in range(num_noise):
            noise_x = random.randint(-self.width//2, self.width//2)
            noise_y = random.randint(-self.height//2, self.height//2)
            noise_size = random.randint(*noise_size_range)
            
            # Color variation based on meteor type
            if self.meteor_type == "iron":
                # Metallic streaks for iron meteors
                variation = random.randint(-10, 30)  # More highlights
            else:
                variation = random.randint(-20, 20)
                
            noise_color = (
                min(255, max(0, self.color[0] + self.color_variation + variation)),
                min(255, max(0, self.color[1] + self.color_variation + variation)),
                min(255, max(0, self.color[2] + self.color_variation + variation))
            )
            self.texture_noise.append((noise_x, noise_y, noise_size, noise_color))
            
        # For iron meteors, add metallic streaks
        if self.meteor_type == "iron":
            for _ in range(5):
                start_angle = random.uniform(0, 2 * math.pi)
                length = random.uniform(0.3, 0.8) * self.width
                width = random.randint(1, 3)
                
                # Create a streak of points
                for i in range(0, int(length), 2):
                    noise_x = int(math.cos(start_angle) * i) 
                    noise_y = int(math.sin(start_angle) * i)
                    if -self.width//2 <= noise_x <= self.width//2 and -self.height//2 <= noise_y <= self.height//2:
                        # Metallic highlight color
                        highlight = random.randint(20, 50)
                        noise_color = (
                            min(255, self.color[0] + highlight),
                            min(255, self.color[1] + highlight),
                            min(255, self.color[2] + highlight)
                        )
                        self.texture_noise.append((noise_x, noise_y, width, noise_color))
    
    def update(self):
        super().update()
        self.rotation += self.rotation_speed
        if self.rotation > 360:
            self.rotation -= 360
            
        # Update trail particles for burning meteor effect
        if random.random() < 0.3:  # 30% chance to emit a particle each frame
            # Create trail particles behind the meteor
            self.trail_particles.append([
                self.x + random.uniform(-self.width/4, self.width/4),  # x position
                self.y - self.height/2 - random.uniform(5, 15),  # y position (behind meteor)
                random.uniform(-0.5, 0.5),  # x velocity
                random.uniform(-1, -2),  # y velocity (upward)
                random.uniform(5, 10),  # lifetime
                self.trail_color  # color
            ])
        
        # Update existing trail particles
        for particle in self.trail_particles[:]:
            particle[0] += particle[2]  # Update x position
            particle[1] += particle[3]  # Update y position
            particle[4] -= 0.2  # Decrease lifetime
            
            # Remove dead particles
            if particle[4] <= 0:
                self.trail_particles.remove(particle)
    
    def draw(self, screen):
        # Draw trail particles first (behind the meteor)
        for particle in self.trail_particles:
            # Create a surface for the particle glow
            glow_size = int(particle[4] * 1.5)
            if glow_size <= 0:
                continue
                
            glow_surf = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
            
            # Draw gradient glow
            for radius in range(glow_size, 0, -1):
                alpha = min(255, int(150 * (radius / glow_size) * (particle[4] / 10)))
                color = (particle[5][0], particle[5][1], particle[5][2], alpha)
                pygame.draw.circle(glow_surf, color, (glow_size, glow_size), radius)
            
            # Blit the glow
            screen.blit(glow_surf, (int(particle[0]) - glow_size, int(particle[1]) - glow_size))
        
        # Create a surface for the meteor with per-pixel alpha
        meteor_surf = pygame.Surface((self.width*2, self.height*2), pygame.SRCALPHA)
        
        # Calculate rotated points
        rotated_points = []
        for x, y in self.points:
            angle = math.radians(self.rotation)
            rotated_x = x * math.cos(angle) - y * math.sin(angle)
            rotated_y = x * math.sin(angle) + y * math.cos(angle)
            rotated_points.append((rotated_x + self.width, rotated_y + self.height))
        
        # Draw glow effect for heated meteors
        if self.has_glow:
            # Draw on screen (larger area than the meteor itself)
            glow_surf = pygame.Surface((self.width*3, self.height*3), pygame.SRCALPHA)
            for radius in range(self.width, 0, -5):
                alpha = self.glow_color[3] * (radius / self.width)
                color = (self.glow_color[0], self.glow_color[1], self.glow_color[2], alpha)
                pygame.draw.circle(glow_surf, color, (self.width*3//2, self.height*3//2), radius)
            screen.blit(glow_surf, (self.x - self.width*3//2, self.y - self.height*3//2))
            
            # Also add a heated edge to the meteor itself
            edge_glow = pygame.Surface((self.width*2, self.height*2), pygame.SRCALPHA)
            pygame.draw.polygon(edge_glow, (255, 150, 0, 100), rotated_points, 0)
            meteor_surf.blit(edge_glow, (0, 0))
        
        # Base color is now the meteor's color with variation
        base_color = (
            min(255, max(0, self.color[0] + self.color_variation)),
            min(255, max(0, self.color[1] + self.color_variation)),
            min(255, max(0, self.color[2] + self.color_variation))
        )
        
        # Create a gradient fill for 3D effect
        for i in range(10):
            # Shrink the points slightly for each layer
            shrink_factor = 1.0 - (i * 0.03)
            inner_points = []
            for x, y in rotated_points:
                dx = x - self.width
                dy = y - self.height
                new_x = self.width + dx * shrink_factor
                new_y = self.height + dy * shrink_factor
                inner_points.append((new_x, new_y))
            
            # Darken the color for inner layers
            layer_color = (
                max(0, base_color[0] - i * 5),
                max(0, base_color[1] - i * 5),
                max(0, base_color[2] - i * 5)
            )
            
            if len(inner_points) >= 3:  # Need at least 3 points for a polygon
                pygame.draw.polygon(meteor_surf, layer_color, inner_points)
            
            # Stop when we get too small
            if shrink_factor < 0.7:
                break
        
        # Draw a slightly darker outline with thickness
        darker_color = (
            max(0, base_color[0] - 50),
            max(0, base_color[1] - 50),
            max(0, base_color[2] - 50)
        )
        pygame.draw.polygon(meteor_surf, darker_color, rotated_points, 3)
        
        # Add texture noise for surface detail
        for noise_x, noise_y, noise_size, noise_color in self.texture_noise:
            # Rotate noise position
            angle = math.radians(self.rotation)
            rotated_x = noise_x * math.cos(angle) - noise_y * math.sin(angle)
            rotated_y = noise_x * math.sin(angle) + noise_y * math.cos(angle)
            
            # Draw the noise detail
            pygame.draw.circle(meteor_surf, noise_color, 
                              (int(rotated_x + self.width), int(rotated_y + self.height)), 
                              noise_size)
        
        # Add crater details with 3D effect
        for crater_x, crater_y, crater_size, crater_color, crater_depth in self.crater_positions:
            # Rotate crater position
            angle = math.radians(self.rotation)
            rotated_x = crater_x * math.cos(angle) - crater_y * math.sin(angle)
            rotated_y = crater_x * math.sin(angle) + crater_y * math.cos(angle)
            
            # Draw crater shadow (offset slightly)
            shadow_color = (
                max(0, crater_color[0] - 50),
                max(0, crater_color[1] - 50),
                max(0, crater_color[2] - 50)
            )
            
            # Create 3D effect with multiple circles
            for i in range(3):
                size_factor = 1.0 - (i * 0.2)
                depth_offset = i * 2
                pygame.draw.circle(meteor_surf, shadow_color, 
                                  (int(rotated_x + self.width + depth_offset), 
                                   int(rotated_y + self.height + depth_offset)), 
                                  int(crater_size * size_factor))
            
            # Draw main crater
            pygame.draw.circle(meteor_surf, crater_color, 
                              (int(rotated_x + self.width), int(rotated_y + self.height)), 
                              crater_size)
            
            # Add highlight to one side of crater for 3D effect
            highlight_color = (
                min(255, crater_color[0] + 40),
                min(255, crater_color[1] + 40),
                min(255, crater_color[2] + 40)
            )
            highlight_offset = crater_size // 3
            pygame.draw.circle(meteor_surf, highlight_color, 
                              (int(rotated_x + self.width - highlight_offset), 
                               int(rotated_y + self.height - highlight_offset)), 
                              crater_size // 3)
        
        # Add type-specific details
        if self.meteor_type == "iron":
            # Add metallic sheen to iron meteors
            for i in range(3):
                # Create random highlight lines
                start_x = random.randint(0, self.width*2)
                start_y = random.randint(0, self.height*2)
                end_x = start_x + random.randint(-self.width//3, self.width//3)
                end_y = start_y + random.randint(-self.height//3, self.height//3)
                
                # Draw highlight
                pygame.draw.line(meteor_surf, (200, 200, 200, 100), 
                               (start_x, start_y), (end_x, end_y), 
                               random.randint(1, 3))
        
        elif self.meteor_type == "stony":
            # Add more texture to stony meteors
            for _ in range(10):
                x = random.randint(0, self.width*2)
                y = random.randint(0, self.height*2)
                size = random.randint(2, 5)
                color = (
                    min(255, base_color[0] + random.randint(-30, 30)),
                    min(255, base_color[1] + random.randint(-30, 30)),
                    min(255, base_color[2] + random.randint(-30, 30))
                )
                pygame.draw.circle(meteor_surf, color, (x, y), size)
        
        # Draw highlights for 3D effect on the top-left portion (light source)
        highlight_points = []
        for x, y in rotated_points:
            # Check if point is in the top-left quadrant relative to center
            if x < self.width and y < self.height:
                highlight_points.append((x-2, y-2))
        
        if len(highlight_points) >= 3:
            pygame.draw.polygon(meteor_surf, (base_color[0] + 40, base_color[1] + 40, base_color[2] + 40), 
                               highlight_points)
        
        # Add heated front edge for atmospheric entry effect
        # Find the bottom-most points
        if self.has_glow:
            bottom_points = []
            for x, y in rotated_points:
                if y > self.height:
                    bottom_points.append((x, y))
            
            if len(bottom_points) >= 2:
                # Sort by x coordinate
                bottom_points.sort()
                
                # Take a subset of points for the heated edge
                if len(bottom_points) > 4:
                    bottom_points = bottom_points[len(bottom_points)//4:3*len(bottom_points)//4]
                
                # Draw heated edge
                for x, y in bottom_points:
                    glow_size = random.randint(3, 6)
                    pygame.draw.circle(meteor_surf, (255, 200, 0, 200), (x, y), glow_size)
        
        # Blit the meteor onto the screen
        screen.blit(meteor_surf, (self.x - self.width, self.y - self.height))

def spawn_meteor():
    x = random.randint(PLAYER_X_MIN, PLAYER_X_MAX)
    return Asteroid(x, -100)
    
# Keep the old function name for compatibility
spawn_asteroid = spawn_meteor

def draw_space(screen):
    # Draw nebula background
    for nebula_cloud in nebula:
        # Create a surface with per-pixel alpha
        cloud_surf = pygame.Surface((nebula_cloud[2]*2, nebula_cloud[2]*2), pygame.SRCALPHA)
        # Draw a soft gradient circle
        for radius in range(nebula_cloud[2], 0, -5):
            alpha = 50 * (radius / nebula_cloud[2])
            color = nebula_cloud[3] + (int(alpha),)
            pygame.draw.circle(cloud_surf, color, (nebula_cloud[2], nebula_cloud[2]), radius)
        # Blit the nebula onto the screen
        screen.blit(cloud_surf, (nebula_cloud[0] - nebula_cloud[2], nebula_cloud[1] - nebula_cloud[2]))
    
    # Draw stars with different brightness and sizes
    for star in stars:
        # Draw a glow effect for larger stars
        if star[2] > 2:
            glow_radius = star[2] * 2
            glow_surf = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
            for r in range(glow_radius, 0, -1):
                alpha = 100 * (r / glow_radius)
                color = (star[3], star[3], star[3], alpha)
                pygame.draw.circle(glow_surf, color, (glow_radius, glow_radius), r)
            screen.blit(glow_surf, (star[0] - glow_radius, star[1] - glow_radius))
        
        # Draw the star itself
        pygame.draw.circle(screen, (star[3], star[3], star[3]), (star[0], star[1]), star[2])
        
        # Make stars twinkle
        star[3] += random.randint(-10, 10)
        if star[3] < 100:
            star[3] = 100
        elif star[3] > 255:
            star[3] = 255

def draw_ui_panel(screen, x, y, width, height, title, content):
    # Draw panel background with rounded corners
    panel_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, (30, 30, 60), panel_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 150), panel_rect, 2, border_radius=10)
    
    # Draw title
    font = pygame.font.SysFont(None, 28)
    title_text = font.render(title, True, WHITE)
    screen.blit(title_text, (x + width//2 - title_text.get_width()//2, y + 10))
    
    # Draw content
    font = pygame.font.SysFont(None, 24)
    content_text = font.render(content, True, WHITE)
    screen.blit(content_text, (x + width//2 - content_text.get_width()//2, y + 40))

def show_game_over(screen, win=False, explosion_time=0):
    # Create semi-transparent overlay with pulsating effect for explosion
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
    if not win and explosion_time < 30:
        # Pulsating red overlay for explosion effect
        alpha = max(0, 180 - explosion_time * 6)  # Fade from 180 to 0
        overlay.fill((255, 0, 0, alpha))
    else:
        # Normal dark overlay
        overlay.fill((0, 0, 0, 180))
    
    screen.blit(overlay, (0, 0))
    
    # Draw game over panel
    panel_width = 400
    panel_height = 300
    panel_x = SCREEN_WIDTH // 2 - panel_width // 2
    panel_y = SCREEN_HEIGHT // 2 - panel_height // 2
    
    # Draw panel background with rounded corners
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(screen, (30, 30, 60), panel_rect, border_radius=15)
    
    # Add glowing border effect for game over
    if not win:
        border_color = (200, 50, 50)  # Red border for game over
        border_pulse = math.sin(pygame.time.get_ticks() * 0.005) * 2 + 3  # Pulsating thickness
    else:
        border_color = (50, 200, 50)  # Green border for win
        border_pulse = 3  # Constant thickness
        
    pygame.draw.rect(screen, border_color, panel_rect, int(border_pulse), border_radius=15)
    
    # Draw header with glow effect
    font = pygame.font.SysFont(None, 74)
    if win:
        text = font.render("YOU WIN!", True, GREEN)
        glow_color = (0, 255, 0, 10)
    else:
        text = font.render("GAME OVER", True, RED)
        glow_color = (255, 0, 0, 10)
    
    # Add text glow
    for offset in range(10, 0, -2):
        glow_surf = pygame.Surface((text.get_width() + offset*2, text.get_height() + offset*2), pygame.SRCALPHA)
        glow_rect = pygame.Rect(offset, offset, text.get_width(), text.get_height())
        pygame.draw.rect(glow_surf, glow_color, glow_rect, border_radius=5)
        screen.blit(glow_surf, (SCREEN_WIDTH // 2 - text.get_width() // 2 - offset, panel_y + 30 - offset))
    
    # Draw the actual text
    screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, panel_y + 30))
    
    # Draw meteor impact message if game over
    if not win:
        font = pygame.font.SysFont(None, 28)
        text = font.render("Your ship was destroyed by a meteor!", True, ORANGE)
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, panel_y + 90))
    
    # Draw score
    font = pygame.font.SysFont(None, 36)
    text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, panel_y + 130))
    
    # Draw high score
    text = font.render(f"High Score: {high_score}", True, YELLOW)
    screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, panel_y + 180))
    
    # Draw restart instruction with pulsating effect
    pulse = math.sin(pygame.time.get_ticks() * 0.01) * 20 + 235  # Pulsate between 215-255
    font = pygame.font.SysFont(None, 36)
    text = font.render("Press SPACE to play again", True, (pulse, pulse, pulse))
    screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, panel_y + 230))

def main():
    global score, game_speed, game_over, high_score
    
    # Set up the game window
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Asteroid Dodge")
    clock = pygame.time.Clock()
    
    # Load or create high score
    if os.path.exists("highscore.txt"):
        try:
            with open("highscore.txt", "r") as f:
                high_score = int(f.read())
        except:
            high_score = 0
    
    # Create player astronaut
    player = Astronaut()
    
    # Falling asteroids
    asteroids = []
    asteroid_spawn_timer = 0
    
    # Particle effects
    particles = []
    
    # Power-up variables
    shield_powerup_timer = random.randint(300, 600)  # 5-10 seconds
    shield_powerup_active = False
    shield_powerup_pos = [0, 0]
    
    # Reset game variables
    score = 0
    game_speed = 5
    game_over = False
    win = False
    game_time = 0
    explosion_time = 0  # Counter for explosion animation
    
    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if not game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        player.move_left()
                    if event.key == pygame.K_RIGHT:
                        player.move_right()
                    if event.key == pygame.K_SPACE:
                        player.activate_shield()
            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    # Save high score
                    if score > high_score:
                        high_score = score
                        with open("highscore.txt", "w") as f:
                            f.write(str(high_score))
                    # Reset the game
                    main()
                    return
        
        # Continuous movement with key presses
        if not game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                player.move_left()
            if keys[pygame.K_RIGHT]:
                player.move_right()
        
        if not game_over:
            game_time += 1
            
            # Update player
            player.update()
            
            # Check if explosion animation is complete
            if player.exploding:
                current_time = pygame.time.get_ticks()
                if current_time - player.explosion_start_time >= player.explosion_duration:
                    game_over = True
            
            # Spawn shield power-up
            shield_powerup_timer -= 1
            if shield_powerup_timer <= 0 and not shield_powerup_active:
                shield_powerup_active = True
                shield_powerup_pos = [random.randint(PLAYER_X_MIN, PLAYER_X_MAX), -50]
            
            # Update shield power-up
            if shield_powerup_active:
                shield_powerup_pos[1] += game_speed
                # Check if player collected power-up
                if abs(shield_powerup_pos[0] - player.x) < 30 and abs(shield_powerup_pos[1] - player.y) < 30:
                    shield_powerup_active = False
                    player.activate_shield()
                    shield_powerup_timer = random.randint(300, 600)
                    # Add particles for power-up collection
                    for _ in range(20):
                        particles.append([
                            shield_powerup_pos[0],
                            shield_powerup_pos[1],
                            random.uniform(-2, 2),
                            random.uniform(-2, 2),
                            random.randint(5, 10),
                            (100, 150, 255)
                        ])
                # Remove if off screen
                if shield_powerup_pos[1] > SCREEN_HEIGHT + 50:
                    shield_powerup_active = False
                    shield_powerup_timer = random.randint(300, 600)
            
            # Spawn asteroids
            asteroid_spawn_timer += 1
            if asteroid_spawn_timer >= 40:  # Spawn a new asteroid more frequently
                asteroids.append(spawn_asteroid())
                asteroid_spawn_timer = 0
            
            # Update asteroids
            for asteroid in asteroids[:]:
                asteroid.update()
                
                # Check if asteroid is off screen
                if asteroid.y > SCREEN_HEIGHT + 100:
                    asteroids.remove(asteroid)
                    score += 10
                
                # Check collision with player
                if asteroid.rect.colliderect(player.rect):
                    if player.shield_active:
                        # Destroy asteroid with shield
                        asteroids.remove(asteroid)
                        score += 5
                        # Add explosion particles
                        for _ in range(20):
                            particles.append([
                                asteroid.x,
                                asteroid.y,
                                random.uniform(-3, 3),
                                random.uniform(-3, 3),
                                random.randint(5, 15),
                                (255, 165, 0)
                            ])
                    else:
                        # Start explosion but don't set game_over yet
                        # We'll set it after the explosion animation
                        explosion_start_time = pygame.time.get_ticks()
                        
                        # Create massive explosion effect
                        # First wave - bright center
                        for _ in range(30):
                            particles.append([
                                player.x,
                                player.y,
                                random.uniform(-8, 8),  # Faster particles
                                random.uniform(-8, 8),
                                random.randint(15, 25),  # Longer lifetime
                                (255, 255, 200)  # Bright yellow-white
                            ])
                        
                        # Second wave - orange/red flames
                        for _ in range(40):
                            particles.append([
                                player.x + random.uniform(-10, 10),
                                player.y + random.uniform(-10, 10),
                                random.uniform(-6, 6),
                                random.uniform(-6, 6),
                                random.randint(10, 20),
                                (255, random.randint(50, 150), 0)  # Orange variations
                            ])
                        
                        # Third wave - smoke and debris
                        for _ in range(30):
                            particles.append([
                                player.x + random.uniform(-15, 15),
                                player.y + random.uniform(-15, 15),
                                random.uniform(-3, 3),
                                random.uniform(-3, 3),
                                random.randint(20, 40),  # Longer lasting smoke
                                (100, 100, 100, 150)  # Gray smoke
                            ])
                            
                        # Add meteor fragments
                        for _ in range(15):
                            particles.append([
                                asteroid.x,
                                asteroid.y,
                                random.uniform(-5, 5),
                                random.uniform(-5, 5),
                                random.randint(10, 20),
                                asteroid.color  # Same color as the meteor
                            ])
                            
                        # Remove the asteroid that caused the collision
                        asteroids.remove(asteroid)
                        
                        # Set player to exploding state
                        player.exploding = True
                        player.explosion_start_time = explosion_start_time
            
            # Update particles
            for particle in particles[:]:
                particle[0] += particle[2]  # x position
                particle[1] += particle[3]  # y position
                particle[4] -= 0.5  # lifetime
                if particle[4] <= 0:
                    particles.remove(particle)
            
            # Increase game speed gradually
            if score > 0 and score % 100 == 0:
                game_speed += 0.2
            
            # Check win condition
            if score >= win_score:
                game_over = True
                win = True
                if score > high_score:
                    high_score = score
        
        # Draw everything
        screen.fill(DARK_BLUE)  # Space background
        draw_space(screen)
        
        # Draw particles
        for particle in particles:
            pygame.draw.circle(screen, particle[5], (int(particle[0]), int(particle[1])), int(particle[4]))
        
        # Draw shield power-up
        if shield_powerup_active:
            # Draw glowing effect
            for radius in range(20, 5, -5):
                alpha = 100 * (radius / 20)
                glow_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (100, 150, 255, alpha), (radius, radius), radius)
                screen.blit(glow_surf, (shield_powerup_pos[0] - radius, shield_powerup_pos[1] - radius))
            # Draw shield icon
            pygame.draw.circle(screen, LIGHT_BLUE, (int(shield_powerup_pos[0]), int(shield_powerup_pos[1])), 10)
            pygame.draw.circle(screen, WHITE, (int(shield_powerup_pos[0]), int(shield_powerup_pos[1])), 10, 2)
        
        # Draw UI panels
        draw_ui_panel(screen, 20, 20, 150, 70, "SCORE", str(score))
        
        # Draw progress to win
        progress = min(score / win_score, 1.0)
        draw_ui_panel(screen, SCREEN_WIDTH - 170, 20, 150, 70, "PROGRESS", f"{int(progress * 100)}%")
        pygame.draw.rect(screen, (50, 50, 80), (SCREEN_WIDTH - 160, 60, 130, 20), border_radius=5)
        pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH - 160, 60, int(130 * progress), 20), border_radius=5)
        
        # Draw shield status if active
        if player.shield_active:
            draw_ui_panel(screen, SCREEN_WIDTH // 2 - 75, 20, 150, 70, "SHIELD", f"{player.shield_timer // 60}s")
        
        # Draw player and asteroids
        player.draw(screen)
        for asteroid in asteroids:
            asteroid.draw(screen)
        
        # Show game over screen
        if game_over:
            if not win:
                explosion_time += 1  # Increment explosion animation counter
            show_game_over(screen, win, explosion_time)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

def show_start_screen(screen):
    # Create a surface for the stars background
    screen.fill(DARK_BLUE)
    draw_space(screen)
    
    # Create title text with glow effect
    title_font = pygame.font.SysFont(None, 100)
    title_text = title_font.render("SPACE DODGE", True, WHITE)
    
    # Draw glow effect
    for offset in range(10, 0, -2):
        glow_surf = pygame.Surface((title_text.get_width() + offset*2, title_text.get_height() + offset*2), pygame.SRCALPHA)
        glow_color = (100, 100, 255, 10)
        glow_rect = pygame.Rect(offset, offset, title_text.get_width(), title_text.get_height())
        pygame.draw.rect(glow_surf, glow_color, glow_rect, border_radius=10)
        screen.blit(glow_surf, (SCREEN_WIDTH//2 - title_text.get_width()//2 - offset, 100 - offset))
    
    # Draw title
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
    
    # Draw animated astronaut
    astronaut = Astronaut()
    astronaut.x = SCREEN_WIDTH // 2
    astronaut.y = SCREEN_HEIGHT // 2
    
    # Draw instructions panel
    instructions_panel = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT - 200, 400, 150)
    pygame.draw.rect(screen, (30, 30, 60), instructions_panel, border_radius=15)
    pygame.draw.rect(screen, (100, 100, 150), instructions_panel, 3, border_radius=15)
    
    # Draw instructions
    font = pygame.font.SysFont(None, 30)
    text = font.render("Arrow Keys: Move Left/Right", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT - 180))
    
    text = font.render("Space: Activate Shield (when available)", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT - 140))
    
    text = font.render("Press SPACE to Start", True, GREEN)
    screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT - 100))
    
    # Draw astronaut
    astronaut.update()
    astronaut.draw(screen)
    
    # Draw asteroid examples
    for i in range(3):
        asteroid = Asteroid(200 + i*200, 350)
        asteroid.draw(screen)
    
    pygame.display.flip()
    
    # Wait for player to start
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False

if __name__ == "__main__":
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Asteroid Dodge")
    
    # Show start screen
    show_start_screen(screen)
    
    # Start the game
    main()
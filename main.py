import asyncio
import pygame
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GAME_SPEED_TICKS = 60
POOP_SIZE = 50
CHARACTER_SIZE = 50

pygame.init()
pygame.mixer.init()
# The screen where all the graphics will be drawn
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
# sets the background of the screen, try updating this for something more beautiful!
background_image = pygame.image.load('assets/background.jpg')
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT)).convert()

players = pygame.sprite.Group()
enemies = pygame.sprite.Group()
poops = pygame.sprite.Group()
clock = pygame.time.Clock()


class Poop(pygame.sprite.Sprite):
    ''' Represents the poop projectiles fired by the player.'''
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load('assets/poop.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (POOP_SIZE, POOP_SIZE))
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        '''This method is called by the event loop below, driven by the loop in main().
        This is called ever frame. Read the pyGame documentation for more details on a frame.
        TL;DR: A frame is one iteration of the game loop, which is typically 1/60th of a second.
        Our job here to update the poop's position, orientation, color, live-or-death
        etc properties as needed.
        '''
        self.rect.y -= 4 # Move upward
        if self.rect.bottom < 0: self.kill() # Remove if off-screen

class Player(pygame.sprite.Sprite):
    ''' Represents the player character, which is a cannon that can move left and right and fire poops.
    
    Notice that it's very similar to Poop? They both inherit from pygame.sprite.Sprite, and they both
    have an image and a rect. The main difference is that the Player has more complex behavior in its
    update() method, and it also has a hit() method to play a sound when it gets hit by an enemy.
    '''

    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('assets/cannon.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (CHARACTER_SIZE, CHARACTER_SIZE))
        self.rect = self.image.get_rect(center=(400, 550))
        self.ticks = pygame.time.get_ticks()

    def _shoot(self):
        # This is a hack to avoid shooting too many poops.
        # The problem: The event loop in main tick 60 times per second. So update() is called
        # 60 times per second. A key or fingermotion can easily last more than 1/60th of a second.
        # In that case multiple poops are fired for just a single key press or finger motion, which
        # is not what we want. So we add a cooldown of 5 ticks
        # Alternatively, we can have a variable to track the last timestampe of fire and adjsut.
        # We have a similar problem for playing sounds when poops hit the enemies, I didn't do anything
        # to fix that so the sounds effect is werid :) Anyone reading this can try to fix that as an
        # exercise! Hint: you can add a timestamp to the Enemy class and check the cooldown before
        # playing the sound. Advanced hint: we can also create a `lock` for sounds or shooting poops,
        # the first call would hold the lock and perform the action. The lock is released after a we
        # know that the action is done. That way will avoid duplicated actions. Locking is a common
        # technique in programming, especially important in multi-threading and asynchronous programming.
        if pygame.time.get_ticks() - self.ticks > 5 * GAME_SPEED_TICKS:
            self.ticks = pygame.time.get_ticks()
            Poop(self.rect.x + CHARACTER_SIZE / 2, self.rect.y).add(poops)


    def update(self):
        # Handle keyboard input for movement and firing.
        # For a phone with a touch screen no keys will be pressed and the code is a no-op.
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.rect.x -= 5
        if keys[pygame.K_RIGHT]: self.rect.x += 5
        if keys[pygame.K_SPACE]: self._shoot()
        
        # For a touch screen, we should be able to detect finger movement and move the player
        # accordingly. This code is a no-op for a device without a touch screen.
        # Consume the list of fingermotion events but only act on the last one. In theory 
        finger_touches = pygame.event.get(eventtype=pygame.FINGERMOTION)
        if len(finger_touches) > 0:
        # finger_touches = pygame.event.get(eventtype=pygame.FINGERDOWN)
        # if len(finger_touches) > 0:
            event = finger_touches[-1]
            # event.x is between 0 and 1, representing the relative position of the finger
            # on the screen.
            self.rect.x = event.x * SCREEN_WIDTH
            # No key for firing on a touch screen. Change to shooting on any movements.
            self._shoot()

        # Keep player within screen bounds
        self.rect.clamp_ip(screen.get_rect())
        
    def hit(self):
        ''' This method is called by in the event loop when the player gets hit by an enemy.

        In this method we define the sepcific behavior that happens when the player gets hit.
        In this case, we simply play a sound effect.
        '''
        sound = pygame.mixer.Sound('assets/game-over.ogg')
        sound.play()

class Enemy(pygame.sprite.Sprite):
    ''' Represents the enemy characters, which are monsters that move downward and can be hit by poops.
    
    Now do you see the pattern? Enemy is also a Sprite, and it has an image and a rect. It also has an
    update() method. Do you see how nice classes and inheritance can be? We can reuse a lot of code and
    just change the parts that are different. This is one of the main benefits of object-oriented
    programming (OOP).  This pattern can also significantly simplify our code and make things much more
    intuitive.
    '''
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load('assets/monster.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (CHARACTER_SIZE, CHARACTER_SIZE))
        self.rect = self.image.get_rect(center=(x, y))
        self.is_hit = False

    def update(self):
        self.rect.y += 5 # Move downward
        if self.rect.top > SCREEN_HEIGHT: self.kill() # Remove if off-screen

    def hit(self):
        sound = pygame.mixer.Sound('assets/ough-hit.ogg')
        sound.play()


# The main game loop, which is the heart of our game. This is where we will handle events,
# update the game state, and render everything on the screen. The async is only needed
# when the code executed in a browser, so that we can yield control back to the browser
# to keep the UI responsive. But the async wouldn't hurt local execution either.
async def main():
    player = Player()
    # Add the player to a group b/c pygame.sprite.groupcollide only works with groups.
    players.add(player)

    # Technically we don't need running now and just use break.
    # Please feel free to add other features to utitlize the running
    # variable, such as a pause menu or a game over screen.
    running = True
    while running:
        # Only check for QUIT event here to avoid consuming other events that are handled
        # elsewhere, such as key presses and finger motions.
        if pygame.event.get(eventtype=pygame.QUIT):
            running = False
        
        # random.random() generates a random number between 0 and 1, so this means
        # we have a 20% chance to spawn an enemy every frame.
        # The enimies can also be added in its own thread and loop. Feel free to try that!
        if random.random() >= 0.8:
            # Spawn an enemy at a random x position at the top (y=50) of the screen.
            k = Enemy(SCREEN_WIDTH * random.random(), 50)
            enemies.add(k)

        # Check to see if anyone dies
        player_hits = pygame.sprite.groupcollide(players, enemies, True, True)

        # pygame.sprite.groupcollide returns a dictionary of all the sprites in
        # the first group that collided with sprites in the second group.
        # we have to decide what to do when a collision happens. In this case,
        # we simply call the hit() method of the Sprite and the behavior will be
        # handled accordingly depending on the type of the Sprite. This is another
        # example of how OOP can help us write clean and intuitive code.
        for player in player_hits.keys():
            player.hit()
        enemy_hits = pygame.sprite.groupcollide(enemies, poops, True, True)
        for enemy in enemy_hits.keys():
            enemy.hit()

        # Update
        players.update()
        poops.update()
        enemies.update()
        
        # In each iteration the whole screen is redrawn, including the background and all
        # Sprites on the screen. This is similar to how a movie works, where each frame is
        # a still image, and when you play the movie, it shows the frames in quick succession
        # to create the illusion of motion.
        screen.blit(background_image, (0, 0))
        players.draw(screen)
        enemies.draw(screen)
        poops.draw(screen)
        pygame.display.flip()
        clock.tick(GAME_SPEED_TICKS)
        await asyncio.sleep(0)  # Yields control to the browser if playing inside a browser.
    pygame.quit()

# Entry point
if __name__ == "__main__":
    asyncio.run(main())
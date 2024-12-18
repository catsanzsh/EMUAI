import tkinter as tk
from tkinter import filedialog, messagebox
import time
from PIL import Image, ImageTk
import struct
import numpy as np

class Memory:
    def __init__(self, size):
        self.size = size
        self.memory = bytearray(size)

    def read_byte(self, address):
        return self.memory[address]

    def write_byte(self, address, value):
        self.memory[address] = value

    def read_word(self, address):
        return struct.unpack_from('>H', self.memory, address)[0]

    def write_word(self, address, value):
        struct.pack_into('>H', self.memory, address, value)


class Graphics:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.screen = np.zeros((height, width, 3), dtype=np.uint8)  # Changed to RGB

    def draw_rectangle(self, x, y, w, h, color):
        # Assuming color is a 24-bit integer (0xRRGGBB)
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        for i in range(y, y + h):
            for j in range(x, x + w):
                if 0 <= i < self.height and 0 <= j < self.width:
                    self.screen[i, j] = [r, g, b]

    def render(self, canvas, image_on_canvas):
        # Convert the screen array to an image and display it on the canvas
        image = Image.fromarray(self.screen, 'RGB')
        photo = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo  # Keep a reference to prevent garbage collection


class Kernel:
    def __init__(self, memory, graphics):
        self.memory = memory
        self.graphics = graphics
        self.registers = [0] * 32  # Example register file

    def decode_instruction(self, instruction):
        opcode = (instruction >> 26) & 0x3F

        if opcode == 0x2D:  # Draw rectangle
            def func():
                # Use modulo operator (%) to wrap coordinates around screen edges
                x = self.registers[1] % self.graphics.width
                y = self.registers[2] % self.graphics.height
                w = self.registers[3]
                h = self.registers[4]
                color = self.registers[5]
                self.graphics.draw_rectangle(x, y, w, h, color)
            return func

        elif opcode == 0x2E:  # Render
            def func():
                self.graphics.render(self.canvas, self.image_on_canvas)
            return func

        elif opcode == 0x02:  # Jump
            def func():
                self.registers[7] = self.registers[7]  # Placeholder for jump logic
            return func

        elif opcode == 0x08:  # Add immediate
            def func():
                rs = (instruction >> 21) & 0x1F
                rt = (instruction >> 16) & 0x1F
                imm = instruction & 0xFFFF
                if imm & 0x8000:  # Sign extension for negative numbers
                    imm -= 0x10000
                self.registers[rt] = self.registers[rs] + imm
            return func

        elif opcode == 0x3F:  # Halt
            def func():
                messagebox.showinfo("Halt", "Program has halted.")
                exit(0)
            return func

        # Return None or appropriate function for other opcodes
        return None

    def execute_program(self, program, canvas, image_on_canvas):
        self.canvas = canvas
        self.image_on_canvas = image_on_canvas
        pc = 0
        while pc < len(program):
            instruction = program[pc]
            func = self.decode_instruction(instruction)
            if func:
                func()
            pc += 1
            time.sleep(0.1)  # Delay for visualization


class GameWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Set the window title as requested
        self.title("ULTRAHLE 20XX [C] TEAM FLAMES [C] 20XX")  # Changed title
        
        # Set window size
        self.geometry("800x600")
        
        # Create a canvas for rendering
        self.canvas = tk.Canvas(self, width=800, height=550, bg="black")
        self.canvas.pack()

        # Add a label for the copyright
        self.copyright_label = tk.Label(
            self, text="© ULTRAHLE 20XX [C] TEAM FLAMES [C] 20XX\nCredit to the big n!",
            justify=tk.CENTER
        )
        self.copyright_label.pack(pady=10)

        # Initialize memory, graphics, and kernel
        memory_size = 1024  # Example size
        self.memory = Memory(memory_size)
        self.graphics = Graphics(800, 550)
        self.kernel = Kernel(self.memory, self.graphics)

        # Define the demo program instructions
        self.demo_program = [
            # Initialize x and y position
            (0x08 << 26) | (1 << 21) | (1 << 16) | 0,        # addi r1, r0, 0  (x = 0)
            (0x08 << 26) | (2 << 21) | (2 << 16) | 0,        # addi r2, r0, 0  (y = 0)
            
            # Set width, height, and color
            (0x08 << 26) | (3 << 21) | (3 << 16) | 50,       # addi r3, r0, 50  (width)
            (0x08 << 26) | (4 << 21) | (4 << 16) | 30,       # addi r4, r0, 30  (height)
            (0x08 << 26) | (5 << 21) | (5 << 16) | 0xFFFF,   # addi r5, r0, 0xFFFF (color - white)
            
            # Clear the screen
            (0x08 << 26) | (6 << 21) | (6 << 16) | 0x0000,   # addi r6, r0, 0x0000 (black color)
            
            (0x2D << 26),                                     # draw rectangle (black)
            (0x2E << 26),                                     # render
            
            (0x08 << 26) | (5 << 21) | (5 << 16) | 0xFFFFFF, # addi r5, r0, 0xFFFFFF (color - white)
            (0x2D << 26),                                     # draw rectangle (white)
            (0x2E << 26),                                     # render
            
            # Increment x and y position
            (0x08 << 26) | (1 << 21) | (1 << 16) | 1,        # addi r1, r1, 1  (x++)
            (0x08 << 26) | (2 << 21) | (2 << 16) | 1,        # addi r2, r2, 1  (y++)
            
            # Jump back to start of loop
            (0x08 << 26) | (7 << 21) | (7 << 16) | -20,      # addi r7, r0, -20 (jump offset)
            (0x02 << 26) | (7 << 21),                        # j r7 (jump back)
            
            (0x3F << 26)                                      # halt
        ]

        # Start executing the program after the main loop starts
        self.after(100, self.start_program)

    def start_program(self):
        # Run the kernel in a separate thread to prevent blocking the GUI
        import threading
        program_thread = threading.Thread(target=self.kernel.execute_program, args=(self.demo_program, self.canvas, None))
        program_thread.start()


if __name__ == "__main__":
    app = GameWindow()
    app.mainloop()

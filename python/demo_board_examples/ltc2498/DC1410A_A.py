# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 14:37:29 2016

@author: noe_q
"""

#from Tkinter import Tk, Frame, BOTH
#from ttk import Button
#
#class DC1410A_GUI(Frame):
#    def __init__(self, parent):
#        Frame.__init__(self, parent, background="grey")
#        self.parent = parent
#        self.parent.title("DC1410A-A")
#        self.pack(fill=BOTH,expand=1)
#        w = 290
#        h = 150
#
#        sw = self.parent.winfo_screenwidth()
#        sh = self.parent.winfo_screenheight()
#        
#        x = (sw - w)/2
#        y = (sh - h)/2
#        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))
#        
#        quitButton = Button(self,text="Quit", command=self.quit)
#        quitButton.place(x=50, y=50)
#        
#
#def main():
#    root = Tk()
#    root.geometry("250x150+300+300")
#    app = DC1410A_GUI(root)
#    root.mainloop()
#
#if __name__ == '__main__':
#    main()

import sys
import random
from PIL import Image, ImageTk
from Tkinter import Tk, Frame, Canvas, ALL, NW


WIDTH = 300
HEIGHT = 300
DELAY = 100
DOT_SIZE = 10
ALL_DOTS = WIDTH * HEIGHT / (DOT_SIZE * DOT_SIZE)
RAND_POS = 27

x = [0] * ALL_DOTS
y = [0] * ALL_DOTS


class Board(Canvas):

    def __init__(self, parent):
        Canvas.__init__(self, width=WIDTH, height=HEIGHT, 
            background="black", highlightthickness=0)
         
        self.parent = parent 
        self.initGame()
        self.pack()
                       
    
    def initGame(self):

        self.left = False
        self.right = True
        self.up = False
        self.down = False
        self.inGame = True
        self.dots = 3
        
        self.apple_x = 100
        self.apple_y = 190

        for i in range(self.dots):
            x[i] = 50 - i * 10
            y[i] = 50
        
        try:
            self.idot = Image.open("dot.png")
            self.dot = ImageTk.PhotoImage(self.idot)    
            self.ihead = Image.open("head.png")
            self.head = ImageTk.PhotoImage(self.ihead)           
            self.iapple = Image.open("apple.png")
            self.apple = ImageTk.PhotoImage(self.iapple) 

        except IOError, e:
            print e
            sys.exit(1)

        self.focus_get()

        self.createObjects()
        self.locateApple()
        self.bind_all("<Key>", self.onKeyPressed)
        self.after(DELAY, self.onTimer)
        

    def createObjects(self):
    
        self.create_image(self.apple_x, self.apple_y, image=self.apple,
            anchor=NW, tag="apple")
        self.create_image(50, 50, image=self.head, anchor=NW,  tag="head")
        self.create_image(30, 50, image=self.dot, anchor=NW, tag="dot")
        self.create_image(40, 50, image=self.dot, anchor=NW, tag="dot")
   

    def checkApple(self):

        apple = self.find_withtag("apple")
        head = self.find_withtag("head")
        
        x1, y1, x2, y2 = self.bbox(head)
        overlap = self.find_overlapping(x1, y1, x2, y2)
            
        for ovr in overlap:
          
            if apple[0] == ovr:
                
                x, y = self.coords(apple)
                self.create_image(x, y, image=self.dot, anchor=NW, tag="dot")
                self.locateApple()
        
    
    def doMove(self):
      
        dots = self.find_withtag("dot")
        head = self.find_withtag("head")
                
        items = dots + head
        
        z = 0
        while z < len(items)-1:
            c1 = self.coords(items[z])
            c2 = self.coords(items[z+1])
            self.move(items[z], c2[0]-c1[0], c2[1]-c1[1])
            z += 1

        if self.left:
            self.move(head, -DOT_SIZE, 0)
            
        if self.right: 
            self.move(head, DOT_SIZE, 0)

        if self.up:
            self.move(head, 0, -DOT_SIZE)

        if self.down:
            self.move(head, 0, DOT_SIZE)
            

    def checkCollisions(self):

        dots = self.find_withtag("dot")
        head = self.find_withtag("head")
        
        x1, y1, x2, y2 = self.bbox(head)
        overlap = self.find_overlapping(x1, y1, x2, y2)
        
        for dot in dots:
            for over in overlap:
                if over == dot:
                  self.inGame = False
            
        if x1 < 0:
            self.inGame = False
        
        if x1 > WIDTH - DOT_SIZE:
            self.inGame = False

        if y1 < 0:
            self.inGame = False
        
        if y1 > HEIGHT - DOT_SIZE:
            self.inGame = False
        

    def locateApple(self):
    
        apple = self.find_withtag("apple")
        self.delete(apple[0])
    
        r = random.randint(0, RAND_POS)
        self.apple_x = r * DOT_SIZE
        r = random.randint(0, RAND_POS)
        self.apple_y = r * DOT_SIZE
        
        self.create_image(self.apple_x, self.apple_y, anchor=NW,
            image=self.apple, tag="apple")
                
   
    def onKeyPressed(self, e): 
    
        key = e.keysym

        if key == "Left" and not self.right: 
            self.left = True
            self.up = False
            self.down = False
        

        if key == "Right" and not self.left:
            self.right = True
            self.up = False
            self.down = False
        

        if key == "Up" and not self.down:
            self.up = True
            self.right = False
            self.left = False
        

        if key == "Down" and not self.up: 
            self.down = True
            self.right = False
            self.left = False
            
            
    def onTimer(self):

        if self.inGame:
            self.checkCollisions()
            self.checkApple()
            self.doMove()
            self.after(DELAY, self.onTimer)
        else:
            self.gameOver()            
            
             
    def gameOver(self):

        self.delete(ALL)
        self.create_text(self.winfo_width()/2, self.winfo_height()/2, 
            text="Game Over", fill="white")            


class Nibbles(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)
                
        parent.title('Nibbles')
        self.board = Board(parent)
        self.pack()


def main():

    root = Tk()
    nib = Nibbles(root)
    root.mainloop()  


if __name__ == '__main__':
    main()
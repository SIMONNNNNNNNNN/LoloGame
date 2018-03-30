"""
CSSE1001 Assignment 3
Semester 1, 2017
"""

import tkinter as tk

import model
import view
from game_regular import RegularGame
from game_make13 import Make13Game
from game_lucky7 import Lucky7Game
from game_unlimited import UnlimitedGame

__author__ = "<Zhi Chen>"
__email__ = "<Zhi.chen1@uqconnect.edu.au>"

__version__ = "1.1.2"
from base import BaseLoloApp
from tkinter import messagebox
from highscores import HighScoreManager
import random
import copy
import json


class LoloApp(BaseLoloApp):
    '''LoloApp class for starting a game '''
    def __init__(self,master,game,name=None,grid_view=None,
                                            is_savedgame_score=(False,None)):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
            
            game (model.AbstractGame): The game to play. Defaults to a
                                       game_regular.RegularGame.
                                       
            name (str):          The name to be saved in the highscore or
                                  saved_gamefile
                                  
            grid_view (view.GridView): The view to use for the game. Optional.
            
            is_savedgame_score(bool,int): If true the LoloApp loads a most recent
                                     saved game and its score,
                                     otherwise load a new game.

        """
        
        self._name = name
        master.title('Lolo :: {} Mode'.format(game.get_name()))

        #set default values for following functions
        self._lightning_mode = False
        self._turn_num = 0
        self._lightNo = 1
        self._lightNo_increasing=8
        

        self._logo = LoloLogo(master)
        self._logo.pack(side=tk.TOP)
        

        self._status_bar = StatusBar(master)
        self._status_bar.pack(side=tk.TOP,expand=1,fill=tk.X)
        self._status_bar.set_game(game.get_name())

        
        menubar=tk.Menu(master)
        master.config(menu=menubar)
        filemenu = tk.Menu(menubar)
        menubar.add_cascade(label='File',menu=filemenu)
        filemenu.add_command(label='New Game',command=self.reset)
        filemenu.add_command(label='Save Game',command=self.save_game)
        filemenu.add_command(label='Exit',command=self.exit_game)

        if game.get_name()== 'Regular':
            self._record_gamename = 'regular'
        elif game.get_name()=='Lucky 7':
            self._record_gamename = 'lucky7'
        elif game.get_name()=='Make 13':
            self._record_gamename = 'Make 13'
        elif game.get_name() == 'Unlimited':
            self._record_gamename = 'unlimited'


        #inherit game and grid from parent class.
        super().__init__(master,game,grid_view=None)

       
        #If this class is for loading a saved game,set score of the saved game
        if is_savedgame_score[0]:
            self._game.set_score(is_savedgame_score[1])

        
        self._light_button = tk.Button(master,
                                 text='Lightning({})'.format(self._lightNo),
                                command=self.lightning_mode)
        self._light_button.pack()
        



    def bind_events(self):
        """Binds relevant events."""
        self._grid_view.on('select', self.activate)
        self._game.on('game_over', self.game_over)
        self._game.on('score', self.score)
        self._master.bind_all('<Control-n>',self.reset)
        self._master.bind_all('<Control-l>',self.lightning_mode)


    def activate(self, position):
        """Attempts to activate the tile at the given position.

        Parameters:
            position (tuple<int, int>): Row-column position of the tile.

        Raises:
            IndexError: If position cannot be activated.
        """
        #If lightning button is pressed, use remove function.
        if self._lightning_mode:
            self.remove(position)
            
        else:
            if position is None:
                return

            if self._game.is_resolving():
                return

            if position in self._game.grid:
                
                

                def finish_move():
                    self._grid_view.draw(self._game.grid,
                                        self._game.find_connections())

                def draw_grid():
                    self._grid_view.draw(self._game.grid)

                animation = self.create_animation(
                    self._game.activate(position),
                    func=draw_grid,callback=finish_move)
                try:
                    animation()
                except IndexError:
                    messagebox.showerror(title='Cannot Activate',message=(
                        'Cannot activate position {}'.format(position)))

                #increase one lightning ability every 20 turns
                self._turn_num +=1
                #randomly(5%) increase the number of lightning ability
                random_num = random.random()*100
                self._lightNo_increasing *=2
                if self._turn_num %20 == 0 or 0<int(random_num)<5 \
                or self._turn_num % self._lightNo_increasing== 0:
                        
                    self._lightNo+=1
                    
                    self._light_button.config(fg='black',
                            text='Lightning ({})'.format(self._lightNo))

                


    def lightning_mode(self,e=None):
        if self._lightNo >0:
            self._lightning_mode =True
            self._light_button.config(text='**Striking**')

        
    def remove(self, *positions):
        """Attempts to remove the tiles at the given positions.

        Parameters:
            *positions (tuple<int, int>): Row-column position of the tile.

        Raises:
            IndexError: If position cannot be activated.
        """
        
        
        #eliminate one tile when lightning ability available
        if len(positions) is None:
            return

        if self._game.is_resolving():
            return
       
        def finish_move():
            self._grid_view.draw(self._game.grid)

        def draw_grid():
            self._grid_view.draw(self._game.grid)

        animation = self.create_animation(self._game.remove(*positions),
                                            func=draw_grid,
                                            callback=finish_move)
        animation()
        
        #decrease the number of lightning ability after using it until 0
        self._lightNo -=1
        self._lightning_mode =False
        self._light_button.config(
            text='Lightning ({})'.format(self._lightNo))
        #change button text color when lighning ability is used up
        if self._lightNo == 0:
            self._light_button.config(
                text='Lightning ({})'.format(self._lightNo),fg='gray')


    def reset(self, e=None):
        """Resets the game."""
        self._game.reset()
        
        #redraw a grid view 
        self._grid_view.draw(self._game.grid,
                             self._game.find_connections())
        #reset the default values
        self._lightning_mode = False
        self._turn_num = 0
        self._lightNo = 1
        self._light_button.config(
            text='Lightning ({})'.format(self._lightNo))

    def game_over(self):
        """Handles the game ending with no tile can be avtivated."""
        #show users a messagebox that game ends
        messagebox.showinfo(title='Game Over',
                message='You scored {}!'.format(self._game.get_score()))

        #save score and player's name into json file
        scoremanager = HighScoreManager(gamemode=self._record_gamename)
        scoremanager.record(self._game.get_score(),
                            self._game,name=self._name)
        
      
    def exit_game(self):
        """Handles the game ending which is clicked by user."""
        messagebox.showinfo(title='Game Over',
                message='You scored {}!'.format(self._game.get_score()))
        
        scoremanager = HighScoreManager(gamemode=self._record_gamename)
        scoremanager.record(self._game.get_score(),
                            self._game,name=self._name)
        self._master.destroy()
        
    def score(self, points):
        """Handles increase in score."""
        self._status_bar.set_score(self._game.get_score())       

    def save_game(self):
        """Save game data in json file so that can be replayed again."""
        messagebox.showinfo(title='Game Saved',
                message='You saved your game with score {}!'.format(
                                                    self._game.get_score()))

        savemanager = HighScoreManager(file="savedgame.json",
                                       gamemode=self._record_gamename)
        savemanager.record(self._game.get_score(),
                               self._game,name=self._name)


    
class StatusBar(tk.Frame):
    '''Status bar for presenting game mode and current score'''
    def __init__(self,master):
        """
        Parameters:
            master(tk.Frame):The frame that the logo will be put in 

        """            
        super().__init__()
        
        #create two labels, one for game mode, the other for score
        self._label1=tk.Label(self,text='Game')
        self._label1.pack(side=tk.LEFT,padx=0)
        self._label2=tk.Label(self,text='Score: 0')
        self._label2.pack(side=tk.RIGHT,padx=0)
       
       
    def set_game(self,name):
        """
        Set the game name label according to the class to be loaded in 
        
        Parameters:
            game(game* class):game loaded in a class where
            this stutas bar will be used
        
        """ 
        self._label1.config(text='{} Mode'.format(name))
        
    def set_score(self,score):
        """
        Set the game score label 
        
        Parameters:
            score(int):set this value to the game score label
        
        """ 
        self._label2.config(text='Score: {}'.format(score))
        
class LoloLogo(tk.Canvas):
    '''Logo of the LoloGame'''
    def __init__(self,master,loadingmode=False):
        """
        Parameters:
            master(tk.Frame):The frame that the logo will be put in 


        """
        super().__init__()
        #set size of the logo
        self.configure(width=400, height=100)
        self.pack()

        #draw 'lolo' on the canvas
        self.create_rectangle(65,10,85,90,fill='purple',width=0)
        self.create_rectangle(85,70,120,90,fill='purple',width=0)
        self.create_oval(135,30,195,90,fill='purple',width=0)
        self.create_oval(150,45,180,75,fill='white',width=0)
        self.create_rectangle(215,10,235,90,fill='purple',width=0)
        self.create_rectangle(235,70,270,90,fill='purple',width=0)
        self.create_oval(285,30,345,90,fill='purple',width=0)
        self.create_oval(300,45,330,75,fill='white',width=0)

        self._loadingmode = loadingmode

        #modify color if the class is used in loading screen
        if self._loadingmode:
            self.create_oval(150,45,180,75,fill='gray',width=0)
            self.create_oval(300,45,330,75,fill='gray',width=0)
            self.config(bg='gray')

            
        

class AutoPlayingGame(BaseLoloApp):
    '''Auto playing class for a game'''
    def __init__(self,master,game,grid_view=None,loadingmode=False):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
            
            game (model.AbstractGame): The game to play. Defaults to a
                                       game_regular.RegularGame.
                                                                        
            grid_view (view.GridView): The view to use for the game. Optional.
            
            loadingmode(bool): If true the layout changes colour
                                     

        """
        super().__init__(master,game,grid_view=None)
        self._move_delay =0
        self.resolve()
        self._loadingmode = loadingmode
        if self._loadingmode== True:
            self._master.config(bg='gray')

    def bind_events(self):
        """Binds relevant events."""
        self._game.on('resolve',self.resolve)

    def resolve(self,delay=None):
        """Makes a move after a given movement delay"""
        if delay is None:
            delay = self._move_delay
        self._master.after(delay,self.move)
    def move(self):
        """Finds a connected tile randomly and activates it"""
        connections=list(self._game.find_groups())
        if connections:
            """pick random valid move"""
            cells = list()
            for connection in connections:
                for cell in connection:
                    cells.append(cell)
            self.activate(random.choice(cells))
        else:
            self._game.reset()
            self._grid_view.draw(self._game.grid,
                                 self._game.find_connections())
            self.resolve()
            
class LoloApp2(AutoPlayingGame):
    '''Loading screen of the game'''
    def __init__(self,master,game,grid_view=None,loadingmode=True):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
            
            game (model.AbstractGame): The game to play. Defaults to a
                                       game_regular.RegularGame.
                                       
            name (str):          The name to be saved in the highscore or
                                  saved_gamefile
                                  
            grid_view (view.GridView): The view to use for the game. Optional.
            
            loadingmode(bool): If true the layout changes colour

         """
        master.title('Lolo :: {} Mode'.format(game.get_name()))
        self._game =game                       
        #deep copy a loading screen game for starting a new game
        self._lologame = copy.deepcopy(self._game)

        self._logo = LoloLogo(master,loadingmode=True)
        self._logo.config(highlightthickness=0)
        self._logo.pack(side=tk.TOP)
        
        self._inputframe = tk.Frame(master)
        self._inputframe.pack()
        self._namelabel = tk.Label(self._inputframe,text='Your Name:',bg='gray',
                                   fg='white',highlightthickness=0)
        self._namelabel.pack(side=tk.LEFT)
        self._entry = tk.Entry(self._inputframe)
        self._entry.pack(side=tk.RIGHT)

        #button frame containing a series of buttons
        self._buttonframe = tk.Frame(master,padx=100,bg='gray')
        self._buttonframe.pack(side=tk.LEFT,expand=1,fill=tk.BOTH)     
        self._playgamebutton = tk.Button(self._buttonframe,text='Play Game',
                                         width=30,command=self.start_game)
        self._playgamebutton.pack(side=tk.TOP,expand=1)
                         
        self._gamemode = tk.Button(self._buttonframe,width=30,
                                    text='Load the Saved Game',
                                   command=self.load_game)
                                   
                                   
        self._gamemode.pack(side=tk.TOP,expand=1)

        self._hightscore = tk.Button(self._buttonframe,
                                     width=30,text='Hight Scores',
                                     command=self.highscore)
        self._hightscore.pack(side=tk.TOP,expand=1)
        self._gamemode = tk.Button(self._buttonframe,width=30,
                                    text='Choose Game Mode',
                                   command=self.gamemode)
                                   
                                   
        self._gamemode.pack(side=tk.TOP,expand=1)
        
        self._exitgame = tk.Button(self._buttonframe,text='Exit Game',
                                   width=30,command=self.quit)
        self._exitgame.pack(side=tk.TOP,expand=1)

        #inherit game and grid from parent class
        super().__init__(master,self._game,grid_view=None,loadingmode=True)            
        self._grid_view.config(bg='gray')
        
    def start_game(self):
        """start to play a game"""
        name = self._entry.get()
        start_game = self._lologame
        self._master.destroy()
        root=tk.Tk()
        app=LoloApp(root,start_game,name)
        

    def gamemode(self):
        '''A window for choosing a game mode'''
        
        root=tk.Toplevel()
        self._gamemode_frame =root
        root.title('Choose Game Mode')
        label = tk.Label(root,text='Choose a game mode:')
        label.pack(side=tk.TOP)
        self._mode = tk.StringVar()
        self._mode.set('Regular')
        tk.Radiobutton(root,text='Regular',variable=self._mode,
                       value='Regular').pack(side=tk.TOP)
        tk.Radiobutton(root,text='Make 13',variable=self._mode,
                       value='Make13').pack(side=tk.TOP)
        tk.Radiobutton(root,text='Lucky 7',variable=self._mode,
                       value='Lucky7').pack(side=tk.TOP)
        tk.Radiobutton(root,text='Unlimited',variable=self._mode,
                       value='Unlimited').pack(side=tk.TOP)
        tk.Button(root,text='Ok',command=self.getmode).pack(side=tk.TOP)
        
    def getmode(self):
        '''Apply game mode chosen from gamemode function'''
        if self._mode.get() == 'Regular':
            self._game = RegularGame()
        elif self._mode.get() == 'Make13':
            self._game = Make13Game()
        elif self._mode.get() == 'Lucky7':
            self._game = Lucky7Game()
        if self._mode.get() == 'Unlimited':
            self._game = UnlimitedGame()

        self._lologame = copy.deepcopy(self._game)
        self._grid_view.destroy()
        self._grid_view = view.GridView(self._master, self._game.grid.size())
        self._grid_view.pack()
        self._grid_view.draw(self._game.grid, self._game.find_connections())
        self._grid_view.config(bg='gray')
        
        self._game.on('resolve',self.resolve)
        self._gamemode_frame.destroy()

    def load_game(self):
        '''load a recent saved game for selected game mode'''
        loadgame = self._lologame
        self._master.destroy()
        root = tk.Tk()
        if self._game.get_name()== 'Regular':
            self._record_gamename = 'regular'
        elif self._game.get_name()=='Lucky 7':
            self._record_gamename = 'lucky7'
        elif self._game.get_name()=='Make 13':
            self._record_gamename = 'Make 13'
        elif self._game.get_name() == 'Unlimited':
            self._record_gamename = 'unlimited'


        saved_games_data = HighScoreManager(file='savedgame.json',
                                        gamemode=self._record_gamename)
        
        #Since the data is saved in file in sequence by time,
        #the last one should be the most rently played.
        #If no saved in the file, except an error.
        try:
            
            saved_game_data = saved_games_data.get_data()[-1]
            saved_game = self._game.deserialize(saved_game_data['grid'])
            
            app=LoloApp(root,saved_game,is_savedgame_score=(True,
                                                    saved_game_data['score']))
        except IndexError:
            
            messagebox.showerror(title='No Saved Game',
                                 message=('You have not saved any game'))
            
            root.destroy()


    def highscore(self):
        """popup window of highscores"""
        root = tk.Toplevel()
        app = highscore_interface(root,self._game)
        

    def quit(self):
        """Quit the loading screen"""
        self._master.destroy()
        

    
class highscore_interface(tk.Frame):
    """
        Highscore data class for displaying screenshot of best player
        and other highscores
    """
    def __init__(self,master,game, grid_view=None):
        """
        Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
            game (model.AbstractGame): The game to play. Defaults to a
                                       game_regular.RegularGame.
            grid_view (view.GridView): The view to use for the game. Optional.


        """
        master.title('Leaderboard')
        self._master = master

        #look for game data from file according to game's name
        if game.get_name()== 'Regular':
            highscore_mode = 'regular'
        elif game.get_name()=='Lucky 7':
            highscore_mode = 'lucky7'
        elif game.get_name()=='Make 13':
            highscore_mode = 'Make 13'
        elif game.get_name() == 'Unlimited':
            highscore_mode = 'unlimited'
        
              
        self._highscore = HighScoreManager(gamemode=highscore_mode)  
        highest = self._highscore.get_sorted_data()[0]
      
        self._bestplayer = tk.Label(master,
            text='Best Player: {} with {} points!'.format(highest['name'],
                                                          highest['score']))
        self._bestplayer.pack()
        self._grid_list = highest['grid']
        
        if game is None:
            game = RegularGame(types=3)
        self._game = game
        
        grid_view = view.GridView(master, self._game.grid.size())
        self._grid_view = grid_view
        self._grid_view.pack()

        highscore_game = self._game.deserialize(self._grid_list)
        self._grid_view.draw(highscore_game.grid)

        #leader board displaying a number of high scores
        self._title= tk.Label(master,text='Leaderboard')
        self._title.pack()
        self._leaderboard = tk.Frame(master)
        self._leaderboard.pack(fill=tk.BOTH)
        self._leaderboard_name = tk.Frame(self._leaderboard)
        self._leaderboard_name.pack(side=tk.LEFT)
        self._leaderboard_score = tk.Frame(self._leaderboard)
        self._leaderboard_score.pack(side=tk.RIGHT)
        
        for name in self._highscore.get_sorted_data():
            name = tk.Label(self._leaderboard_name,text=name['name'])
            name.pack(anchor=tk.NW)
        for score in self._highscore.get_sorted_data():
            score = tk.Label(self._leaderboard_score,text=score['score'])
            score.pack(anchor=tk.NE)
  
def main():
    game = RegularGame()
    root = tk.Tk()
    app = LoloApp2(root,game)
    root.mainloop()

if __name__ == "__main__":
    main()

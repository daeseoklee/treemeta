#from kivy.logger import Logger, LOG_LEVELS

#Logger.setLevel(LOG_LEVELS[""])

import kivy
kivy.require('2.0.0')
from kivy.app import App

from kivy.properties import ObjectProperty,ListProperty,NumericProperty,StringProperty,BooleanProperty 

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput

from kivy.clock import Clock

from kivy.metrics import dp

from metatree_core import *

from choicewidget import ChoiceWidget
from explorerstate import ExplorerState
from settingswindow import SettingsWindow
from edititemwindow import EditItemWindow
from explorer import *

import time


class WindowManager(ScreenManager):
  state_manager=ObjectProperty() #given as __init__ argument
  state=ObjectProperty() 
  main=ObjectProperty()
  settings=ObjectProperty()

  def __init__(self,**kwargs):
    super(WindowManager,self).__init__(**kwargs)
    #self.main=MainWindow()
    pass

  
  def switch_state(self,i):
    self.state=self.state_manager.load_state(i)
    self.main.content.choicestate=app.root.state.make_choicestate()
    self.main.content.after_init()
  pass
  def replace_screen(self,name,screen):
    assert screen.name==name   
    names=[screen.name for screen in self.screens]
    assert name in names
    idx=names.index(name)
    screen.manager = self
    screen.bind(name=self._screen_name_changed)
    self.screens[idx]=screen

  def open_edititemwindow(self,path,new):
    choicestate=self.state.make_choicestate()
    self.replace_screen('edititem',EditItemWindow(windowmanager=self,state=self.state,path=path,new=new))
    self.transition.direction='up'
    self.current='edititem'



class MainWindow(Screen):
  menubar=ObjectProperty()
  content=ObjectProperty()
  choicestate=ObjectProperty()
  windowmanager=ObjectProperty()
  pass





class MainWindowContent(Screen):
  choicestate=ObjectProperty()
  windowmanager=ObjectProperty()
  choicewidget=ObjectProperty()
  explorer=ObjectProperty()


  def __init__(self,**kwargs):
    super(MainWindowContent,self).__init__(**kwargs)
    Clock.schedule_once(self.after_init)
  def after_init(self,dt):
    explorerstate=ExplorerState(self.choicestate)
    self.explorer.update_explorerstate(explorerstate)
    self.update_ui()
  def update_ui(self):
    self.choicewidget.update_ui()
    self.explorer.update_ui()
    
class MainChoiceWidget(ChoiceWidget):
  explorer=ObjectProperty()
  def on_choicestate_updated(self):
    self.explorer.update_ui()
  

from pathlib import Path

class TreeMeta(App):
  def build(self):
    sm=StateManager(str(Path(__file__).parent.parent/'config'/'config.txt'))
    #state=sm.load_default_state()
    #state=State('config/b.mtr','config/b_favorites.csv','config/b_metadata.csv')
    wm=WindowManager(state_manager=sm)
    return wm


if __name__=='__main__':
  app=TreeMeta()
  app.run()
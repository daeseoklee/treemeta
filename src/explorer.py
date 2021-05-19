import kivy
kivy.require('2.0.0')

from kivy.properties import ObjectProperty,ListProperty,NumericProperty,StringProperty,BooleanProperty 

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput

from metatree_core import *
from explorerstate import ExplorerState

from os.path import basename

from kivy.lang import Builder 
Builder.load_file('explorer.kv')

from time import sleep

class Explorer(BoxLayout):
  explorerstate=ObjectProperty() #given from main.py
  show_unmatched=BooleanProperty()
  top=ObjectProperty()
  windowmanager=ObjectProperty()
  viewmanager=ObjectProperty()
  edit_mode=BooleanProperty()
  def update_explorerstate(self,explorerstate):
    self.explorerstate=explorerstate
    #don't have to call update_ui here since it will be called by MainWindowContent
  def update_ui(self):
    self.top.update_ui()
    screen=self.viewmanager.get_screen(self.viewmanager.current)
    screen.update_ui()
  pass
class ExplorerTop(BoxLayout):
  root=ObjectProperty()
  leftcorner=ObjectProperty()
  middlelabel=ObjectProperty()
  rightcorner=ObjectProperty()
  def update_ui(self):
    self.middlelabel.text=self.root.explorerstate.get_pathstr()
    if self.root.explorerstate.at_the_root():
      if self.leftcorner in self.children:
        self.remove_widget(self.leftcorner)
    else:
      if not self.leftcorner in self.children:
        self.add_widget(self.leftcorner,index=len(self.children))
    self.rightcorner.update_ui()
    pass
  def on_release_prevdir(self):
    self.root.explorerstate.exit_currentdir()
    self.root.update_ui()
  pass
class ExplorerTopRightCorner(BoxLayout):
  root=ObjectProperty()
  def update_ui(self):
    self.clear_widgets()
    if not self.root.edit_mode:
      self.add_widget(ExplorerEditButton(root=self.root))
    else:
      self.add_widget(ExplorerEditRootButton(root=self.root))
      self.add_widget(ExplorerEditReturnButton(root=self.root))

class ExplorerEditButton(Button):
  root=ObjectProperty() #given as init argument
  def on_press_this(self):
    self.root.edit_mode=True
    self.root.update_ui()
  pass
class ExplorerEditRootButton(Button):
  root=ObjectProperty() #given as init argument
  def on_press_this(self):
    self.explorerstate:ExplorerState
    state=self.root.explorerstate.state
    rootdirname=self.root.explorerstate.rootdirname
    if rootdirname in state.registered_dirs:
      new=False 
    else:
      new=True
    self.root.windowmanager.open_edititemwindow(rootdirname,new)
  pass 
class ExplorerEditReturnButton(Button):
  root=ObjectProperty() #given as init argument
  def on_press_this(self):
    self.root.edit_mode=False
    self.root.update_ui()
    pass
  pass 

class ExplorerManager(ScreenManager):
  pass 

class ExplorerListView(Screen):
  root=ObjectProperty()
  l=ObjectProperty()
  def update_ui(self):
    self.l.update_ui()
  pass 
class ExplorerListViewList(BoxLayout):
  root=ObjectProperty() #Explorer
  view=ObjectProperty()
  def update_ui(self):
    self.clear_widgets()
    matched_dirs,unmatched_dirs,unregistered_dirnames,matched_files,unmatched_files,unregistered_filenames=self.root.explorerstate.get_entries()
    for dir in matched_dirs:
      self.add_widget(ExplorerListViewMatchedDir(view=self.view,is_registered=True,is_dir=True,path=dir.path,item=dir))
    for file in matched_files:
      self.add_widget(ExplorerListViewMatchedFile(view=self.view,is_registered=True,is_dir=False,path=file.path,item=file))
    for dirname in unregistered_dirnames:
      self.add_widget(ExplorerListViewUnregisteredDir(view=self.view,is_registered=False,is_dir=True,path=dirname))
    for filename in unregistered_filenames:
      self.add_widget(ExplorerListViewUnregisteredFile(view=self.view,is_registered=False,is_dir=False,path=filename))
    if self.root.show_unmatched:
      for dir in unmatched_dirs:
        self.add_widget(ExplorerListViewUnmatchedDir(view=self.view,is_registered=True,is_dir=True,path=dir.path,item=dir))
      for file in unmatched_files:
        self.add_widget(ExplorerListViewUnmatchedFile(view=self.view,is_registered=True,is_dir=False,path=file.path,item=file))
#listview entries-----------------------------

class ExplorerListViewEntry(BoxLayout):
  view=ObjectProperty() #given as init argument
  is_registered=BooleanProperty() #given as init arugment
  is_dir=BooleanProperty() #given as init argument 
  path=StringProperty() #given as init argument
  def __init__(self,**kwargs):
    super(ExplorerListViewEntry,self).__init__(**kwargs)
    if self.view.root.edit_mode:
      if self.is_registered:
        #Field self.item exists 
        if not self.item.registered_children: #either [] or None
          self.add_widget(ExplorerListViewEntryUnregisterButton(entry=self),index=len(self.children)) 
        pass
      parent_dirname=abspath(join(self.path,pardir))
      state=self.view.root.explorerstate.state
      if parent_dirname in state.registered_dirs:
        self.add_widget(ExplorerListViewEntryEditButton(entry=self))
  def on_press_edit(self):
    windowmanager=self.view.root.windowmanager
    windowmanager.open_edititemwindow(path=self.path,new=not self.is_registered)
  def on_release_enter(self):
    if self.is_dir:
      self.view.root.explorerstate.enter_dir(basename(self.path))
      self.view.root.update_ui()
    else:
      pass
  def on_release_unregister(self):
    self.view.root.explorerstate.state.unregister_path(self.path)
    self.view.root.explorerstate.state.save_metadata()
    self.view.root.update_ui()
  pass
class ExplorerListViewEntryUnregisterButton(Button):
  entry=ObjectProperty() #given as init argument
  pass
class ExplorerListViewEntryEditButton(Button):
  entry=ObjectProperty() #given as init argument
  pass
class ExplorerListViewMatchedDir(ExplorerListViewEntry):
  item=ObjectProperty() #given as init arugment
  def __init__(self,**kwargs):
    super(ExplorerListViewMatchedDir,self).__init__(**kwargs)
    pass
  pass 
class ExplorerListViewUnmatchedDir(ExplorerListViewEntry):
  item=ObjectProperty() #given as init argument
  def __init__(self,**kwargs):
    super(ExplorerListViewUnmatchedDir,self).__init__(**kwargs)
    pass
  pass
class ExplorerListViewUnregisteredDir(ExplorerListViewEntry):
  def __init__(self,**kwargs):
    super(ExplorerListViewUnregisteredDir,self).__init__(**kwargs)
    pass
  pass 
class ExplorerListViewMatchedFile(ExplorerListViewEntry):
  item=ObjectProperty() #given as init argument
  def __init__(self,**kwargs):
    super(ExplorerListViewMatchedFile,self).__init__(**kwargs)
    pass
  pass 
class ExplorerListViewUnmatchedFile(ExplorerListViewEntry):
  item=ObjectProperty() #given as init argument
  def __init__(self,**kwargs):
    super(ExplorerListViewUnmatchedFile,self).__init__(**kwargs)
    pass
  pass
class ExplorerListViewUnregisteredFile(ExplorerListViewEntry):
  def __init__(self,**kwargs):
    super(ExplorerListViewUnregisteredFile,self).__init__(**kwargs)
    pass
  pass 
#--------------------------------------------------

class ExplorerItemView(Screen):
  root=ObjectProperty()
  def update_ui(self):
    pass
  pass
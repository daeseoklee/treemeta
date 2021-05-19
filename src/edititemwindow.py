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

from os.path import basename

from metatree_core import *
from choicewidget import ChoiceWidget


from kivy.lang import Builder 
Builder.load_file('edititemwindow.kv')

class Success(Exception):
  pass 
class EditItemWindow(Screen):
  windowmanager=ObjectProperty() #given as init argument
  state=ObjectProperty() #given as init argument
  path=StringProperty() #given as init argument
  new=BooleanProperty() #given as init argument
  choicestate=ObjectProperty() #given as init argument
  content=ObjectProperty()
  top=ObjectProperty()
  submittable=BooleanProperty()
  conflict_message=StringProperty()
  def __init__(self,**kwargs):
    super(EditItemWindow,self).__init__(**kwargs)
    Clock.schedule_once(self.after_init)
  def after_init(self,dt):
    if not self.new:
      if isdir(self.path):
        assert self.path in self.state.registered_dirs
        item=self.state.registered_dirs[self.path]
      else:
        assert self.path in self.state.registered_files
        item=self.state.registered_files[self.path]
      self.choicestate.fit_metadata(item.metadata)
    self.content.choicewidget.on_choicestate_updated()
    self.content.choicewidget.update_ui()
    self.top.update_ui()

  def update_submittable(self):
    try:
      metadata=self.choicestate.partial_metadata
      if self.new:
        self.state.assert_may_register_path(self.path,metadata)
        
      else:
        self.state.assert_may_edit_path_metadata(self.path,metadata)
      raise Success()
    except MetadataEditException as e:
      self.submittable=False 
      self.conflict_message='{} "{}" has value {} at "{}"'.format('Parent' if e.problem=='parent_conflict' else 'Child',basename(e.conflict_path),e.other_n,e.conflict_node_id)
    except Success:
      self.submittable=True
      self.conflict_message=''
    except Exception as e:
      raise e
  def on_release_most_general(self):
    if self.path==self.state.rootdirname:
      self.choicestate.revert_all()
    else:
      parent_dirname=abspath(join(self.path,pardir))
      assert parent_dirname in self.state.registered_dirs
      parent=self.state.registered_dirs[parent_dirname]
      self.choicestate.fit_metadata(parent.metadata)

    self.content.choicewidget.on_choicestate_updated()
    self.content.choicewidget.update_ui()
    self.top.update_ui()
    pass
  def on_release_submit(self):
    self.choicestate:ChoiceState
    self.state:State
    metadata=self.choicestate.partial_metadata
    if self.new:
      self.state.register_path(self.path,metadata)
    else:
      self.state.edit_path_metadata(self.path,metadata)
    self.windowmanager.main.content.update_ui()
    self.state.save_metadata()
    self.manager.transition.direction='down'
    self.windowmanager.current='main'
    pass
  def on_release_return(self):
    self.manager.transition.direction='down'
    self.manager.current='main'
  pass

class EditItemWindowTop(BoxLayout):
  root=ObjectProperty()
  path=StringProperty()
  firstbox=ObjectProperty()
  secondbox=ObjectProperty()
  submit_button=ObjectProperty()
  def __init__(self,**kwargs):
    super(EditItemWindowTop,self).__init__(**kwargs)
    Clock.schedule_once(self.after_init)
  def after_init(self,dt):
    self.submit_button=SubmitButton(root=self.root)
    self.secondbox=ErrorMessageMenu() 
    
  def update_ui(self):
    self.secondbox.message=self.root.conflict_message
    if self.root.submittable:
      if not self.submit_button in self.firstbox.children:
        self.firstbox.add_widget(self.submit_button,index=1)
      if self.secondbox in self.children:
        self.remove_widget(self.secondbox)
    else:
      if self.submit_button in self.firstbox.children:
        self.firstbox.remove_widget(self.submit_button)
      if not self.secondbox in self.children:
        self.add_widget(self.secondbox)
  pass

class SubmitButton(Button):
  root=ObjectProperty() #given as init argument, EditItemWindow
  pass 
class ErrorMessageMenu(BoxLayout):
  message=StringProperty() #given as init argument
  pass 

class EditItemContent(BoxLayout):
  root=ObjectProperty()
  choicewidget=ObjectProperty()
  choicestate=ObjectProperty()
  def __init__(self,**kwargs):
    super(EditItemContent,self).__init__(**kwargs)
    pass
  pass

class EditItemChoiceWidget(ChoiceWidget):
  root=ObjectProperty() #EditItemWindow
  def __init__(self,**kwargs):
    super(EditItemChoiceWidget,self).__init__(**kwargs)
    Clock.schedule_once(self.after_init)
  def after_init(self,dt):
    self.update_ui()
  def on_choicestate_updated(self):
    self.root.update_submittable()
    self.root.top.update_ui()
    pass 
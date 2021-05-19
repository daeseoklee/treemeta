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

from kivy.lang import Builder 
Builder.load_file('choicewidget.kv')

class Status():
  def __init__(self,name):
    self.name=name

class ChoiceWidget(BoxLayout):
  choicestate=ObjectProperty() #when dynamic, given as init argument
  status=ObjectProperty()
  favorites_scroll=ObjectProperty()
  favorites_list=ObjectProperty()
  decided_scroll=ObjectProperty()
  decided_list=ObjectProperty()
  to_decide_scroll=ObjectProperty()
  to_decide_list=ObjectProperty()
  current_selected_node=ObjectProperty()
  def __init__(self,**kwargs):
    super(ChoiceWidget,self).__init__(**kwargs)
    #Clock.schedule_once(self.after_init)
  #def after_init(self,dt):
  #  self.update_ui()
  def new_status(self,name):
    return Status(name)
  def update_ui(self):
    #self.on_choicestate_updated() #check carefully if this line applies everytime this method is called
    self.favorites_list.clear_widgets()
    self.decided_list.clear_widgets() 
    self.to_decide_list.clear_widgets()
    #'favorites' scroll
    self.favorites_list.add_widget(FavoritesConfigureBox(choicestate=self.choicestate,choice_widget=self,status=self.status))
    for node in self.choicestate.active_favorites:
      favorites=self.choicestate.favorites[node]
      self.favorites_list.add_widget(FavoritesBox(choicestate=self.choicestate,choice_widget=self,basenode=node,favorites=favorites,status=self.status))
    #self.favorites_scroll.height=self.#favorites_list.minimum_height
    #'decided' scroll
    for decision in self.choicestate.decided:
      if decision.is_favorite:
        widget=FavoriteDecisionBox(choicestate=self.choicestate,choice_widget=self,decision=decision)
      elif decision.base.is_multiple_choice:
        widget=MultipleChoiceDecisionBox(choicestate=self.choicestate,choice_widget=self,decision=decision)
      else:
        widget=SingleDecisionBox(choicestate=self.choicestate,choice_widget=self,decision=decision)
      self.decided_list.add_widget(widget)

    #'to_decide' scroll 
    for node in self.choicestate.to_decide:
      if node.is_multiple_choice:
        widget=MultipleChoiceQuestionBox(choicestate=self.choicestate,choice_widget=self,node=node)
        widget.update_active()
      else:
        widget=SingleQuestionBox(choicestate=self.choicestate,choice_widget=self,node=node)
      self.to_decide_list.add_widget(widget)  
  
  def on_choicestate_updated(self): #change outside this widget
    pass 
  pass



#'favorites' scroll---------------------- 
class FavoritesList(BoxLayout):
  #mode=NumericProperty()
  pass

class FavoritesConfigureBox(BoxLayout):
  choicestate=ObjectProperty()
  choice_widget=ObjectProperty()
  status=ObjectProperty()
  favorite_name_textinput=ObjectProperty()
  def __init__(self,**kwargs):
    super(FavoritesConfigureBox,self).__init__(**kwargs)
    self.add_widget(FavoritesConfigureButtons(root=self))
    if self.status.name=='add_favorite':
      self.favorite_name_textinput=NewFavoriteNameTextInput(root=self)
      self.add_widget(self.favorite_name_textinput)
      #here--------------------
  def on_release_remove_favorite(self):
    self.status.name='remove_favorite'
    self.choice_widget.update_ui()
    
  def on_release_return_remove_favorite(self):
    self.status.name='default'
    self.choice_widget.update_ui()
  def on_release_add_favorite(self):
    self.status.name='add_favorite'
    self.choice_widget.update_ui()
  def on_release_return_add_favorite(self):
    self.status.name='default'
    self.choice_widget.update_ui()
  def on_release_do_add_favorite(self):
    global app
    current_selected_node=self.choice_widget.current_selected_node
    if current_selected_node==None or (not current_selected_node in [decision.base for decision in self.choicestate.decided]):
      raise Exception('node not selected') #error message box
    basenode=self.choice_widget.current_selected_node
    name=self.favorite_name_textinput.text
    self.choicestate.add_current_as_favorite(basenode,name)
    self.choicestate.state.save_favorites()
    self.status.name='default'
    self.choice_widget.on_choicestate_updated()
    self.choice_widget.update_ui()
    print(self.choicestate.favorites)

class FavoritesConfigureButtons(BoxLayout):
  root=ObjectProperty()
  pass
  def __init__(self,**kwargs):
    super(FavoritesConfigureButtons,self).__init__(**kwargs)
    if self.root.status.name=='default':
      self.add_widget(RemoveFavoriteButton(root=self.root))
      self.add_widget(AddFavoriteButton(root=self.root))
    elif self.root.status.name=='add_favorite':
      self.add_widget(ReturnAddFavoriteButton(root=self.root))
      self.add_widget(DoAddFavoriteButton(root=self.root))
    elif self.root.status.name=='remove_favorite':
      self.add_widget(ReturnRemoveFavoriteButton(root=self.root))
class AddFavoriteButton(Button):
  root=ObjectProperty()
  pass
class RemoveFavoriteButton(Button):
  root=ObjectProperty()
  pass 
class ReturnAddFavoriteButton(Button):
  root=ObjectProperty()
  pass
class DoAddFavoriteButton(Button):
  root=ObjectProperty()
  pass
class NewFavoriteNameTextInput(TextInput):
  root=ObjectProperty()
  pass
class ReturnRemoveFavoriteButton(Button):
  root=ObjectProperty()
  pass 


class FavoritesBox(BoxLayout):
  choicestate=ObjectProperty() #given as init argument
  choice_widget=ObjectProperty() #given as init argument
  basenode=ObjectProperty() #given as init argument
  favorites=ObjectProperty()#given as init argument
  status=ObjectProperty() #given as init argument
  base_box=ObjectProperty()
  favorites_selection_box=ObjectProperty()
  def __init__(self,**kwargs):
    super(FavoritesBox,self).__init__(**kwargs)
    self.favorites_selection_box=FavoritesSelectionBox(root=self,favorites=self.favorites)
  def on_press_updown(self):
    if not self.base_box.open:
      self.add_widget(self.favorites_selection_box)
    else:
      self.remove_widget(self.favorites_selection_box)
    self.base_box.open=not self.base_box.open
class FavoritesBaseBox(BoxLayout):
  open=BooleanProperty(False)
  pass
class FavoritesSelectionBox(BoxLayout):
  root=ObjectProperty() #given as init argument
  favorites=ObjectProperty() #given as init argument
  def __init__(self,**kwargs):
    super(FavoritesSelectionBox,self).__init__(**kwargs)
    for favorite in self.favorites:
      self.add_widget(FavoriteBox(root=self.root,favorite=favorite))
class FavoriteBox(BoxLayout):
  root=ObjectProperty() #given as init argument
  favorite=ObjectProperty() #given as init argument
  def __init__(self,**kwargs):
    super(FavoriteBox,self).__init__(**kwargs)
    if self.root.status.name=='remove_favorite':
      self.add_widget(DoRemoveFavoriteButton(root=self.root,favorite=self.favorite,choice_widget=self.root.choice_widget))

class FavoriteApplyButton(Button):
  root=ObjectProperty() #given by kv
  favorite=ObjectProperty() #given by kv
  def __init__(self,**kwargs):
    super(FavoriteApplyButton,self).__init__(**kwargs)
    Clock.schedule_once(self.after_init)
  def after_init(self,dt):
    assert self.favorite.is_favorite
  def on_release_this(self):
    self.root.choicestate.apply_favorite(self.root.basenode,self.favorite)
    self.root.choice_widget.on_choicestate_updated()
    self.root.choice_widget.update_ui()
class DoRemoveFavoriteButton(Button):
  root=ObjectProperty() #given as init argument
  favorite=ObjectProperty() #given as init argument
  choice_widget=ObjectProperty() #given as init argument
  def on_release_this(self):
    self.root.choicestate.remove_favorite(self.root.basenode,self.favorite)
    self.root.choicestate.state.save_favorites()
    self.root.status.name='default'
    self.choice_widget.on_choicestate_updated()
    self.choice_widget.update_ui()


#'decided' scroll-------------------------

class DecidedList(BoxLayout):
  #mode=NumericProperty()
  pass 
class SingleDecisionBox(BoxLayout):
  choicestate=ObjectProperty() #given as init argument
  choice_widget=ObjectProperty() #given as init argument
  decision=ObjectProperty() #given as init argument
  basename_box=ObjectProperty()
  def __init__(self,**kwargs):
    super(SingleDecisionBox,self).__init__(**kwargs)
    Clock.schedule_once(self.after_init)
  def after_init(self,dt):
    if self.choice_widget.status.name=='add_favorite':
      self.basename_box.add_widget(SelectNodeCheckBox(choice_widget=self.choice_widget,node=self.decision.base,group=self.choice_widget.favorites_list))
  def on_revert_release(self):
    self.choicestate.revert(self.decision)
    self.choice_widget.on_choicestate_updated()
    self.choice_widget.update_ui()
  pass
class SelectNodeCheckBox(CheckBox):
  choice_widget=ObjectProperty(None) #given as init argument
  node=ObjectProperty(None) #given as init argument
  def update_current_selected_node(self):
    self.choice_widget.current_selected_node=self.node
class MultipleChoiceDecisionBox(BoxLayout):
  choicestate=ObjectProperty() #given as init argument
  choice_widget=ObjectProperty() #given as init argument
  decision=ObjectProperty() #given as init argument
  labels=ObjectProperty()
  basename_box=ObjectProperty()
  def __init__(self,**kwargs):
    super(MultipleChoiceDecisionBox,self).__init__(**kwargs)
    for subnode,n in self.decision.seq[1:]:
      if n==0:
        choice='any'
      elif n==1:
        choice='yes'
      elif n==2:
        choice='no'
      text='{} : {}'.format(subnode.name,choice)
      self.labels.add_widget(MultipleChoiceDecisionLabel(text=text))
    Clock.schedule_once(self.after_init)
  def after_init(self,dt):
    if self.choice_widget.status.name=='add_favorite':
      self.basename_box.add_widget(SelectNodeCheckBox(choice_widget=self.choice_widget,node=self.decision.base,group=self.choice_widget.favorites_list))
  def on_revert_release(self):
    self.choicestate.revert(self.decision)
    self.choice_widget.on_choicestate_updated()
    self.choice_widget.update_ui()
  pass 
class MultipleChoiceDecisionLabel(Label):
  pass
class FavoriteDecisionBox(BoxLayout):
  choicestate=ObjectProperty() #given as init argument
  choice_widget=ObjectProperty() #given as init argument
  decision=ObjectProperty() #given as init argument
  basename_box=ObjectProperty()
  def __init__(self,**kwargs):
    super(FavoriteDecisionBox,self).__init__(**kwargs)
    self.decision:Decision

    Clock.schedule_once(self.after_init)
  def after_init(self,dt):
    if self.choice_widget.status.name=='add_favorite':
      self.basename_box.add_widget(SelectNodeCheckBox(choice_widget=self.choice_widget,node=self.decision.base,group=self.choice_widget.favorites_list))
    
  def on_revert_release(self):
    self.choicestate.revert(self.decision)
    self.choice_widget.on_choicestate_updated()
    self.choice_widget.update_ui()
  pass 


#'to_decide' scroll-----------------------

class ToDecideList(BoxLayout):
  #mode=NumericProperty()
  pass 
class SingleQuestionBox(BoxLayout):
  choicestate=ObjectProperty() #given as init argument
  choice_widget=ObjectProperty() #given as init argument
  node=ObjectProperty() #given as init argument
  def __init__(self,**kwargs):
    super(SingleQuestionBox,self).__init__(**kwargs)
    assert not self.node.is_multiple_choice
    self.node:TreeNode
    if self.node.allow_any:
      button=SingleQuestionEntry(choicestate=self.choicestate,choice_widget=self.choice_widget,node=self.node,n=0)
      self.add_widget(button) 
    for n in range(1,1+len(self.node.options)):
      button=SingleQuestionEntry(choicestate=self.choicestate,choice_widget=self.choice_widget,node=self.node,n=n)
      self.add_widget(button)
class SingleQuestionEntry(Button):
  choicestate=ObjectProperty() #given as init argument
  choice_widget=ObjectProperty() #given as init argument
  node=ObjectProperty() #given as init argument
  n=NumericProperty(0) #given as init argument

  def on_release(self):
    self.choicestate.decide(self.node,self.n)
    self.choice_widget.on_choicestate_updated()
    self.choice_widget.update_ui()

class MultipleChoiceQuestionBox(BoxLayout):
  choicestate=ObjectProperty() #given as init argument
  choice_widget=ObjectProperty() #given as init argument
  node=ObjectProperty() #given as init argument
  submit_button=ObjectProperty()
  def __init__(self,**kwargs):
    super(MultipleChoiceQuestionBox,self).__init__(**kwargs)
    assert self.node.is_multiple_choice
    assert len(self.node.options)==1
    subnodes=self.node.options[0].children
    for i in range(len(subnodes)):
      self.add_widget(MultipleChoiceQuestionEntry(choicestate=self.choicestate,choice_widget=self.choice_widget,node=self.node,subnode_idx=i))
  def update_active(self):
    assert self.node in self.choicestate.chosenlists
    for widget in self.children:
      if type(widget)==MultipleChoiceQuestionEntry:
        widget.activate_n(self.choicestate.chosenlists[self.node][widget.subnode_idx])
  def on_release_submit(self):
    self.choicestate.decide_multiple_choice(self.node)
    self.choice_widget.on_choicestate_updated()
    self.choice_widget.update_ui()
class MultipleChoiceQuestionEntry(BoxLayout):
  choicestate=ObjectProperty() #given as init argument
  choice_widget=ObjectProperty() #given as init argument
  node=ObjectProperty() #given as init argument
  subnode_idx=NumericProperty() #given as init argument 
  allow_any=BooleanProperty(True)
  checkbox_list=ListProperty([])
  
  def __init__(self,**kwargs):
    super(MultipleChoiceQuestionEntry,self).__init__(**kwargs)
    subnode=self.node.options[0].children[self.subnode_idx]
    self.allow_any=subnode.allow_any
    if self.allow_any:
      self.add_widget(MultipleChoiceQuestionEntryLabel(text='any'))
      checkbox=MultipleChoiceQuestionEntryCheckBox(group=self,n=0)
      self.add_widget(checkbox)
      self.checkbox_list.append(checkbox)
    self.add_widget(MultipleChoiceQuestionEntryLabel(text='y'))
    checkbox=MultipleChoiceQuestionEntryCheckBox(group=self,n=1)
    self.add_widget(checkbox)
    self.checkbox_list.append(checkbox)
    self.add_widget(MultipleChoiceQuestionEntryLabel(text='n'))
    checkbox=MultipleChoiceQuestionEntryCheckBox(group=self,n=2)
    self.add_widget(checkbox)
    self.checkbox_list.append(checkbox)
  def get_n_from_checkbox(self,checkbox):
    assert checkbox in self.checkbox_list
    i=self.checkbox_list.index(checkbox)
    if self.allow_any:
      return i
    return 1+i
  def activate_checkbox(self,checkbox):
    assert checckbox in self.checkbox_list
    pass 
  def activate_n(self,n):
    if self.allow_any:
      self.checkbox_list[n].active=True
    else:
      self.checkbox_list[n-1].active=True
  def update_n(self,n):
    self.choicestate.chosenlists[self.node][self.subnode_idx]=n
class MultipleChoiceQuestionEntryLabel(Label):
  pass
class MultipleChoiceQuestionEntryCheckBox(CheckBox):
  n=NumericProperty()
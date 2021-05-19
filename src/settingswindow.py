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
Builder.load_file('settingswindow.kv')

class SettingsWindow(Screen):
  pass
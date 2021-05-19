import kivy
kivy.require('2.0.0')

from kivy.uix.widget import Widget 
from kivy.lang import Builder


from kivy.uix.boxlayout import BoxLayout

Builder.load_file('xbox.kv')

class XBox(BoxLayout):
  pass 
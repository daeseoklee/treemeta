import kivy
kivy.require('2.0.0')

from kivy.app import App

from kivy.properties import ObjectProperty,NumericProperty,StringProperty

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

from kivy.clock import Clock

from xbox import XBox

class MainWindow(BoxLayout):
  pass


class XApp(App):
  def build(self):
    return MainWindow()

if __name__=='__main__':
  app=XApp()
  app.run()
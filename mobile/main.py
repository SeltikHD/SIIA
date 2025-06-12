import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

kivy.require('2.3.0')

class Root(BoxLayout):
    def __init__(self):
        super(Root, self).__init__()

    def get_data(self):
        self.temperature_label.text = "Temperatura: 32°C"
        self.moisture_label.text = "Umidade: 60%"

class SIIA(App):
    def build(self):
        return Root()

siia = SIIA()
siia.run()

import pytest
from kivy.uix.button import Button

def test_ui_button_interaction():
    btn = Button(text="Launch Server")
    clicked = False
    
    def on_click(instance):
        nonlocal clicked
        clicked = True
        
    btn.bind(on_press=on_click)
    btn.dispatch('on_press')
    
    assert clicked is True
    assert btn.text == "Launch Server"

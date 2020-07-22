import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from bs4 import BeautifulSoup
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
import plyer
import datetime
import requests
import re
import threading
import shelve
import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')
import matplotlib.pyplot as plt
from kivy.garden.matplotlib.backend_kivy import FigureCanvas

temperature_number_global = None

# Получение температуры
class AccessTempSensor:
    def __init__(self, url):
        self.url = url

    def get_temperature_number(self):
        print(f"get_temperature_number thread is {threading.current_thread()}")
        try:
            # raise requests.exceptions.Timeout()
            page = requests.get(self.url)
            page = BeautifulSoup(page.content, 'html.parser')
            temperature_number = re.search(r'\b\d+\b', str(page.p)).group()
            print(f"Current thread of get_temperature_number function is {threading.current_thread()}")
            global temperature_number_global
            temperature_number_global=temperature_number
            print(f"get_temperature_number value is {temperature_number}")
        except requests.exceptions.RequestException as e:
            print(f"Connection error{e} in get_temperature_number")
            temperature_number_global = f"Connection error{e}"


url='http://192.168.0.120'
furnance = AccessTempSensor(url)

temperature_thread = threading.Thread(target=furnance.get_temperature_number, args=(url,))


notif_settings_number_ph=50
notif_settings_critical_number_ph=60

# Создание интерфейса, сетки
class Float(FloatLayout):
    def __init__(self, **kwargs):
        super(FloatLayout, self).__init__(**kwargs)
        self.buttonstate = False
        self.temperature_state_is_triggered = False
        self.critical_temperature_state_is_triggered = False
        tabloidid = ObjectProperty(None)
        refreshbtnid = ObjectProperty(None)
        refreshingbtnid = ObjectProperty(None)
        testbtnid = ObjectProperty(None)
    def notifications(self):
        if notif_settings_number_ph <= int(temperature_number_global) <= notif_settings_critical_number_ph:
            print("notifications was triggered")
            self.critical_temperature_state_is_triggered = False
            if self.temperature_state_is_triggered == False:
                print("notifications temperature 1 is triggered")
                plyer.notification.notify(title="test title", message=temperature_number_global)
                self.temperature_state_is_triggered = True
            else:
                print("notifications temperature 1 is not triggered")
                pass
        elif int(temperature_number_global) >= notif_settings_critical_number_ph:
            if self.critical_temperature_state_is_triggered == False:
                plyer.notification.notify(title="test title", message=temperature_number_global)
                self.critical_temperature_state_is_triggered = True
                print("notifications critical temperature is triggered")
            else:
                print("notifications critical temperature is not triggered")
                pass
        else:
            print("notifications wasnt triggered")
            self.temperature_state_is_triggered == False
    def temperature_recorder(self):
        currentDT=datetime.datetime.now()
        data = shelve.open("data", writeback=True)
        try:
            data[f"day{currentDT.day}_time"].append(currentDT.strftime("%H:%M:%S"))
            data[f"day{currentDT.day}_temperature"].append(int(temperature_number_global))
            print(data[f"day{currentDT.day}_time"])
            print(data[f"day{currentDT.day}_temperature"])
            print("temperature_recorder found existing file and appended new values to it")
        except:
            data[f"day{currentDT.day}_time"] = [currentDT.strftime("%H:%M:%S")]
            data[f"day{currentDT.day}_temperature"]=[int(temperature_number_global)]
            print("temperature_recorder didnt find existing file and created new one")
        data.close()
    def update_temperature_text(self):
        self.tabloidid.text = temperature_number_global
    # Действие первой кнопки, обновление числа 1 раз
    def refresh_thread(self):
        print(f"refresh_thread thread is {threading.current_thread()}")
        # print("refresh button thread")
        # temperature_thread = threading.Thread(target=furnance.get_temperature_number)
        # temperature_thread.start()
        # temperature_thread.join()
        refresh_thread_inside_thread = threading.Thread(target=furnance.get_temperature_number())
        refresh_thread_inside_thread.start()
        # print(temperature_thread)
        # print(threading.current_thread())

        try:
            int(temperature_number_global)
            self.update_temperature_text()
            self.temperature_recorder()
            self.notifications()
        except:
            self.update_temperature_text()
    # Первая кнопка
    def refresh(self):
        print(f"refresh button thread is {threading.current_thread()}")
        refresh_thread = threading.Thread(target=self.refresh_thread)
        refresh_thread.start()
        print("refresh button was pressed")

    # Действие второй кнопки, постоянное обновление числа
    # callback
    def my_callback(self, time):
        print("Callback called")
        self.refresh()
    # действие кнопки
    def refreshing_thread(self):
        print("refreshing thread has started")
        print(f"refreshing_thread2 thread is {threading.current_thread()}")
        if self.buttonstate == False:
            self.buttonstate = True
            self.refreshingbtnid.text = "Stop refreshing"
            # Это нужно в треде для furnance.get_temperature_number()
            furnance.get_temperature_number()
            self.update_temperature_text()
            self.event = Clock.schedule_interval(self.my_callback, 10 / 1.)
        else:
            self.buttonstate = False
            self.refreshingbtnid.text = "Start refreshing"
            self.event.cancel()
    #Вторая кнопка
    def refreshing(self):
        print(f"refreshing thread is {threading.current_thread()}")
        refreshing_thread2 = threading.Thread(target=self.refreshing_thread)
        refreshing_thread2.start()
        print("refreshing button")
    # График
    def callback_canvas(instance):
        # Clear the existing figure and re-use it
        print("canvas called back")
        plt.clf()
        data = shelve.open("data", writeback=True)
        currentDT = datetime.datetime.now()
        x_axis=data[f"day{currentDT.day}_time"]
        y_axis=data[f"day{currentDT.day}_temperature"]
        x_axis = x_axis[-20:]
        y_axis = y_axis[-20:]
        plt.plot(x_axis, y_axis)
        data.close()
        plt.xticks(rotation=45, ha='right')
        canvas.draw_idle()
fig, ax = plt.subplots()
plt.xticks(rotation=45, ha='right')
plt.plot([],[])
canvas = fig.canvas


class TemperatureSensorApp(App):
    title = 'Temperature sensor'
    def build(self):
        root=Float()
        canvas.pos = (0, root.height * 3)
        canvas.size_hint = (1, 0.5)
        root.add_widget(canvas)
        return root



if __name__ == "__main__":
    TemperatureSensorApp().run()

import pickle
from datetime import datetime, timedelta
import math
from EV import EV


class TestCase:
    def __init__(self, EVs, voltage=220, max_rate=32, period=1):
        self.VOLTAGE = voltage
        self.DEFAULT_MAX_RATE = max_rate
        self.period = period
        self.EVs = EVs

        self.charging_data = {}
        for ev in EVs:
            self.charging_data[ev.session_id] = []

    def step(self, pilot_signals, iteration):
        active_EVs = self.get_active_EVs(iteration)
        for ev in active_EVs:
            charge_rate = ev.charge(pilot_signals[ev.session_id])
            self.charging_data[ev.session_id].append({'time': iteration, 'charge_rate': charge_rate})
        pass


    def get_active_EVs(self, iteration):
        active_EVs = []
        for ev in self.EVs:
            if ev.remaining_demand > 0 and ev.arrival <= iteration and ev.departure > iteration:
                active_EVs.append(ev)
        return active_EVs


    def get_charging_data(self):
        return self.charging_data





def generate_test_case_local(file_name, start, end, voltage=220, max_rate=32, period=1, max_duration=720):
    sessions = pickle.load(open(file_name, 'rb'))
    EVs = []
    uid = 0
    min_arrival = None
    for s in sessions:
        if start <= s[0]-timedelta(hours=7) and s[0]-timedelta(hours=7) <= end and s[2] >= 0.5:
            ev = EV(s[0].timestamp() // 60 // period,
                    (math.ceil(s[1].timestamp() / 60 / period)),
                    ((s[2] * (60/period) * 1e3) / voltage),
                    max_rate,
                    s[3],
                    uid)
            if ev.departure - ev.arrival < ev.requested_energy / ev.max_rate:
                ev.departure = math.ceil(ev.requested_energy / ev.max_rate) + ev.arrival
            uid += 1
            if not min_arrival:
                min_arrival = ev.arrival
            elif min_arrival > ev.arrival:
                min_arrival = ev.arrival
            EVs.append(ev)

    for ev in EVs:
        ev.arrival -= min_arrival
        ev.departure -= min_arrival
        if ev.departure - ev.arrival > max_duration:
            ev.departure = ev.arrival + max_duration
    return TestCase(EVs, voltage, max_rate, period)
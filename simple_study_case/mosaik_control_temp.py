"""
    An entity which loads a timeseries of relative PV production and outputs it when asked
"""

import mosaik_api
from itertools import count
from statistics import mean

META = {
    'models': {
        'ControlTempSim': {
            'public': True,
            'params': ['temp_setpoint',
                       'controller_gain'],
            'attrs': ['T', 'x'],
        },
    },
}


class ControlTempSim(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators = {}
        self.entityparams = {}

    def init(self, sid, step_size=5, eid_prefix="ControlT", verbose=False):
        self.step_size = step_size
        self.eid_prefix = eid_prefix
        self.verbose = verbose
        return self.meta

    def create(
            self, num, model,
            temp_setpoint=22.0,
            controller_gain=0.5):
        counter = self.eid_counters.setdefault(model, count())
        entities = []


        for _ in range(num):
            eid = '%s_%s' % (self.eid_prefix, next(counter))

            esim = {'Tsp': temp_setpoint,
                    'kp': controller_gain,
                    'T': 12,
                    'x': 0}
            self.simulators[eid] = esim

            entities.append({'eid': eid, 'type': model})

        return entities

    ###
    #  Functions used online
    ###

    def step(self, time, inputs):
        for eid, esim in self.simulators.items():
            data = inputs.get(eid, {})
            for attr, incoming in data.items():
                if self.verbose: print("Incoming data:{0}".format(incoming))
                if attr == 'T':
                    Tsp, kp, Tprev = esim['Tsp'], esim['kp'], esim['T']
                    # If multiple units provide us with a measurement,
                    # take the mean.
                    T = mean(incoming.values())
                    newX = (Tsp - T)*kp
                    if newX < 0.1: #stop heater, almost reached the temperature because it is a slow process
                        newX = 0.0
                    elif newX > 1: #set a max val = 1
                        newX = 1.0
                    esim['x'] = newX
                    esim['T'] = T
                    if self.verbose: print("New control input {0}, temp. set point {1} (deltaT={2}) and Kp {3}.".format(newX, Tsp, Tsp - T, kp))
                if attr == 'relSoC':
                    esim['relSoC'] = sum(incoming.values())
            # esim.calc_val(time)

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, esim in self.simulators.items():
            requests = outputs.get(eid, [])
            mydata = {}
            for attr in requests:
                if attr == 'T':
                    mydata[attr] = esim['T']
                elif attr == 'x':
                    mydata[attr] = esim['x']
                else:
                    raise RuntimeError("ControlTempSim {0} has no attribute {1}.".format(eid, attr))
            data[eid] = mydata
        return data

if __name__ == '__main__':
    # mosaik_api.start_simulation(ControlSim())

    test = ControlTempSim()

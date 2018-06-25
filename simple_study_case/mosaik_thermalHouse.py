"""
    An entity which loads a timeseries of relative PV production and outputs it when asked
"""

import mosaik_api
from itertools import count
from my_thermHouse_sim import MyThermHouseSim

META = {
    'models': {
        'ThermalHouseSim': {
            'public': True,
            'params': [
                'ambient_temp', # delete if variable and add to attrs
                'house_insulation_coef',
                'solar_heating_coef',
                'heating_coef',
                't_init'],
            'attrs': ['T', 'zs', 'x'],
        },
    },
}


class ThermalHouseSim(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators = {}
        self.entityparams = {}

    def init(self, sid, step_size=5, eid_prefix="ThermHouE"):
        self.step_size = step_size
        self.eid_prefix = eid_prefix
        
        return self.meta

    def create(
            self, num, model,
            ambient_temp=12, #considered constant
            house_insulation_coef=0.2/3600, # [1/s]
            solar_heating_coef=6.0/3600, # [ºC/s]
            heating_coef=12.0/3600, # [ºC/s]
            t_init=16, # [ºC]
            dt=1.0):
        counter = self.eid_counters.setdefault(model, count())
        entities = []

        # don't know what to change until the end of the function
        for _ in range(num):
            eid = '%s_%s' % (self.eid_prefix, next(counter))

            esim = MyThermHouseSim(
                ambient_temp=ambient_temp,
                house_insulation_coef=house_insulation_coef,
                solar_heating_coef=solar_heating_coef,
                heating_coef=heating_coef,
                dt=dt
                )
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
                if attr == 'x':
                    newXset = min(val for val in incoming.values())
                    esim.x = newXset
                
                if attr == 'zs':
                    newZSset = min(val for val in incoming.values())
                    esim.zs = newZSset
            esim.calc_val(time)

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, esim in self.simulators.items():
            requests = outputs.get(eid, [])
            mydata = {}
            for attr in requests:
                if attr == 'T':
                    mydata[attr] = esim.T
                elif attr == 'x':
                    mydata[attr] = esim.x
                elif attr == 'zs':
                    mydata[attr] = esim.zs
                else:
                    raise RuntimeError("ThermHouseSim {0} has no attribute {1}.".format(eid, attr))
            data[eid] = mydata
        return data

if __name__ == '__main__':
    # mosaik_api.start_simulation(PVSim())

    test = ThermalHouseSim()

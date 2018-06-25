import mosaik
import mosaik.util


SIM_CONFIG = {
    'PVSim': {
        'python': 'mosaik_pv:PVSim',
    },
    'BatterySim': {
        'python': 'mosaik_battery:BatterySim',
    },
    'DemandSim': {
        'python': 'mosaik_demand:DemandSim',
    },
    'GridSim': {
        'python': 'mosaik_grid:GridSim',
    },
    'ControlSim': {
        'python': 'mosaik_control:ControlSim',
    },
    'CollectorSim': {
        'python': 'collector:Collector',
    },
}

END = 24*60*60-1 # 1 hour, 1 MosaikTime = 1 second
# END = 60*60-1 # 1 hour, 1 MosaikTime = 1 second

# Init world
world = mosaik.World(SIM_CONFIG)

## Simulators

## Photovoltaic Producer
# Params:
#   rated_capacity: Rated (maximal) power [kW]
#   seriesname: Name of series in the data store
# Output:
#   P: Current production [kW]
#   Pav: Current maximally available production [kW]
#   Pmax: Current power limit [kW]
# Input:
#   Plimit: Current power limit [kW]
# Desc:
#   Read PV production from a CSV file (=> Pav)
#   P = min(Pav, Plimit)

pv_sim = world.start(
        'PVSim',
        eid_prefix='pv_',
        step_size=1)
pv_entity_1 = pv_sim.PVSim(
        rated_capacity=7,
        series_name='/PV715_20180510')

## Battery
# Params:
#   rated_charge_capacity: Maximum charge power (>0) [kW]
#   rated_discharge_capacity: Maximum discharge power (>0) [kW]
#   rated_capacity: Maximal state of charge (>0) [kWs]
#   initial_charge_rel: Battery fill % at start (in [0,1]) [r.u.]
#   charge_change_rate: Time-delay factor (in [0,1], 1 => instant response)
#   dt: Conversion factor for one time step (default: 1.0/(60*60) = 1sec/time step)
# Output:
#   P: Current production/consumption [kW]
#   SoC: Current state-of-charge (in [0, SoCmax]) [kWs]
# Input:
#   Pset: Current power target [kW]
# Desc:
#   P>0 => the battery is outputting power into the grid (discharging)
#   Pset = Pset bounded to [-Pmax, Pmax]
#   P(t) = kappa*Pset + (1-kappa)*P(t-1) bounded to [-SoC, SoCmax-SoC]
#   SoC(t) = SoC(t-1) + P(t) bounded to [0, SoCmax]

batt_sim = world.start(
        'BatterySim',
        eid_prefix='batt_',
        step_size=1)
batt_entity_1 = batt_sim.BatterySim(
        rated_capacity=10,
        rated_discharge_capacity=30,
        rated_charge_capacity=30,
        initial_charge_rel=0.5,
        charge_change_rate=0.03,
#        dt=1.0/(60*60)
        )

## Demand
# Params:
#   rated_capacity: Maximal power draw (indicative) [kW]
# Output:
#   P: Current power draw [kW]
# Desc:
#   Read demand time series from a CSV file (=> Prel in [0, 1])
#   P = Pmax * Prel

demand_sim = world.start(
        'DemandSim',
        eid_prefix='demand_',
        step_size=1)
demand_entity_1 = demand_sim.DemandSim(rated_capacity=4, seriesname='/flexhouse_20180218')


## Grid model
# Params:
#   droop: Relationship between power draw and voltage change [V/kW] (usually <0)
#   V0: Base voltage [V]
# Output:
#   V: Current voltage at bus [V]
#   Pgrid: Current power draw from the grid [kW]
# Input:
#   P: Current power draw from units (Many connections) [kW]
# Desc:
#   Pgrid = - (P_1 + ... + P_N)
#   V = V0 + droop * Pgrid

grid_sim = world.start(
        'GridSim',
        eid_prefix='grid_',
        step_size=1)
grid_entity_1 = grid_sim.GridSim(V0=240, droop=0.1)

## Controller
# Params:
#   kappa: Time-delay compensation factor (usually in [0, 1], 1 => instant response) [a.u.]
# Input:
#   Pgrid: Current power draw [kW]
#   SoC: Battery state-of-charge [kWs]
# Output:
#   Pset: Battery power setpoint [kW]
# Desc:
#   Psett(t) = kappa * Pgrid + (1 - kappa) * Psett(t-1)

control_sim = world.start(
        'ControlSim',
        eid_prefix='demand_',
        step_size=1)
control_entity_1 = control_sim.ControlSim(setpoint_change_rate=0.50)

## Collector
# Params:
#   Storefilename: String indicating the storage file to use
# Input:
#   GENERIC: Anything can be connected and will be logged
# Desc:
#   TODO: On startup, generate a simulation index number (Look into store?)
#   During simulation, save system state
#   TODO: After simulation, write collected data to disk, and save associated parameters.

collector_sim = world.start(
        'CollectorSim',
        step_size=60,
        save_h5=True,
        h5_storename='datastore',
        h5_panelname='Monitor_SimpleCase_Centralized',
        print_results=False)
collector_entity = collector_sim.Collector()

###
#  Connect components
###

# Connect units to grid busbar
world.connect(demand_entity_1, grid_entity_1, ('P', 'P'))
world.connect(pv_entity_1, grid_entity_1, ('P', 'P'))
world.connect(batt_entity_1, grid_entity_1, ('P', 'P'))

# Connect controller
world.connect(grid_entity_1, control_entity_1, ('Pgrid', 'Pgrid'))
world.connect(control_entity_1, batt_entity_1, ('Pset', 'Pset'), time_shifted=True, initial={'Pset': 0.0})
world.connect(batt_entity_1, control_entity_1, ('relSoC', 'relSoC'))

# Connect to Collector
world.connect(batt_entity_1, collector_entity, ('P', 'BattP'))
world.connect(batt_entity_1, collector_entity, ('SoC', 'BattSoC'))
world.connect(demand_entity_1, collector_entity, ('P', 'DemP'))
world.connect(pv_entity_1, collector_entity, ('P', 'SolarP'))
world.connect(grid_entity_1, collector_entity, ('Pgrid', 'GridP'))

world.run(END)

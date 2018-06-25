class MyThermHouseSim:
    def __init__(
            self,
            ambient_temp=12, #considered constant
            house_insulation_coef=0.2/3600, # [1/s]
            solar_heating_coef=6.0/3600, # [ºC/s]
            heating_coef=12.0/3600, # [ºC/s]
            t_init=12, # [ºC]
            dt=1.0):
        """
            Battery simulator.
            Time is assumed to proceed in integer steps.
            @input:
                rated_capacity: Max volume of charge [kWh]
                rated_discharge_capacity: Max output power [kW]
                rated_charge_capacity: Max input power [kW]
                roundtrip_efficiency: Total roundtrip efficiency [0.0-1.0]
                initial_charge_rel: Charge at time 0 relative to max [0.0 - 1.0]
                charge_change_rate: Rate at which charge follows setpoint,
                    1.0= instant following. [0.0 - 1.0]
                dt: number of hours per time step [h] (default: 1 sec per time step)
        """
        self.Ta = ambient_temp
        self.k = house_insulation_coef
        self.phi_s = solar_heating_coef
        self.phi_h = heating_coef

        # Internal variables
        self.curtime = 0 # Time is assumed to step in integer steps
        self.dt = dt
        self._T = t_init
        self._x = 0
        self._zs = 0

        # Externally visible variables
        self.T_ext = 0
        self.x_ext = 0
        self.zs_ext = 0

    def calc_val(self, t):
        """
        """
        assert type(t) is int
        assert t >= self.curtime, "Must step to time of after or at current time: {0}. Was asked to step to {1}".format(t, self.curtime)
        self._ext_to_int() # Translate external state to internal state
        for _ in range(t - self.curtime):
            self._do_state_update()
        self._int_to_ext() # Translate internal state to external state
        self.curtime = t

    def _do_state_update(self):
        # Current power will slowly rise towards setpoint
        # P = self.alpha * self._Pset + (1 - self.alpha) * self._P
        # self._P = self._limit_P(P)
        self._update_temp()

    """
    def _limit_P(self, P):
        # Limit according to bounds
        P = min(max(P, -self.rated_discharge_capacity), self.rated_charge_capacity)
        # Limit to available charge, roundtrip eff. is applied to output
        P = min(
                max(P, -self._charge * self.eta / self.dt), # Cannot discharge more than we have
                (self.rated_capacity - self._charge)/ self.dt) # Cannot overfill
        return P
    """
    def _update_temp(self):
        
        #somewhere define initial temperature: self.T = T_init
        self._T = self.k*(self.Ta - self._T) + self.phi_s*self._zs + self.phi_h*self._x

    def _ext_to_int(self):
        self._x = self.x_ext
        self._zs = self.zs_ext

    def _int_to_ext(self):
        self.T_ext = self._T
        self.x_ext = self._x
        self.zs_ext = self._zs

    # Getter/setters for external users
    @property
    def T(self):
        return self.T_ext
    
    @property
    def x(self):
        return self.x_ext
    
    @property
    def zs(self):
        return self.zs_ext

    @x.setter
    def x(self, newXset):
        self.x_ext = newXset
        
    @zs.setter
    def zs(self, newZSset):
        self.zs_ext = newZSset
        

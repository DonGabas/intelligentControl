import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class FuzzyC:
    def __init__(self):
        # variables linguisticas con su respectivo universo linguistico
        # universo
        univ_error = np.arange(-35, 35, 0.01)
        univ_delta =  np.arange(-2.01, 2.01, 0.01)
        univ_dutty = np.arange(0, 100, 0.01)
        # variables - 2 entradas 1 salida
        self.error = ctrl.Antecedent(univ_error, 'error')
        self.delta = ctrl.Antecedent(univ_delta, 'delta')
        self.dutty = ctrl.Consequent(univ_dutty, 'dutty')

        ###  términos linguisticos por variable con respectivas funciones de membresía
        #error: negativo, negativo cero, positivo cero, positivo
        self.error['n'] = fuzz.trapmf(self.error.universe, [-35, -35, -4, 0])
        self.error['nz'] = fuzz.trimf(self.error.universe, [-2, -1, 0.3])
        self.error['pz'] = fuzz.trimf(self.error.universe, [-0.3, 1, 2])
        self.error['p'] = fuzz.trapmf(self.error.universe, [0, 4, 35, 35])

        # delta: negativo grande, n pequeño, cero, positivo pequeño, p grande
        self.delta['n'] = fuzz.trapmf(self.delta.universe, [-2.01, -2.01, -1, 0])
        self.delta['c'] = fuzz.trimf(self.delta.universe, [-0.3, 0, 0.3])
        self.delta['p'] = fuzz.trapmf(self.delta.universe, [0, 1, 2.01, 2.01])

        # dutty: pequeño, mediano, grande
        self.dutty['p'] = fuzz.trimf(self.dutty.universe, [0, 0, 27])
        self.dutty['m'] = fuzz.trimf(self.dutty.universe, [24, 45, 70])
        self.dutty['g'] = fuzz.trapmf(self.dutty.universe, [50, 70, 100, 100])

        ########################      reglas linguisticas      ##########################################

        self.rule1 = ctrl.Rule(antecedent=((self.error['n'] & self.delta['n']) |
                              (self.error['n'] & self.delta['c']) |
                              (self.error['n'] & self.delta['p']) |
                              (self.error['nz'] & self.delta['n']) |
                              (self.error['nz'] & self.delta['c']) |
                              (self.error['pz'] & self.delta['n'])),
                  consequent=self.dutty['p'], label='rule pequeña')

        self.rule2 = ctrl.Rule(antecedent=((self.error['nz'] & self.delta['p']) |
                                    (self.error['pz'] & self.delta['c'])),
                        consequent=self.dutty['m'], label='rule mediana')

        self.rule3 = ctrl.Rule(antecedent=((self.error['pz'] & self.delta['p']) |
                                    (self.error['p'] & self.delta['n']) |
                                    (self.error['p'] & self.delta['c']) |
                                    (self.error['p'] & self.delta['p'])),
                        consequent=self.dutty['g'], label='rule grande')
        
        #######################################################################################

        # creacion del controlador difuso acorde a las reglas linguisticas
        self.system = ctrl.ControlSystem(rules=[self.rule1, self.rule2, self.rule3])
        self.sim = ctrl.ControlSystemSimulation(self.system)
    
    def __call__(self, e, de):
        # pasar error y su tasa de cambio como entrada
        self.sim.input['error'] = e
        self.sim.input['delta'] = de

        # calcular la salida - variable de control
        self.sim.compute()
        u = self.sim.output['dutty']

        return u

    def viewCtld(self):
        self.error.view()
        self.delta.view()
        self.dutty.view()
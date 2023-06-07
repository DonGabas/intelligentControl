import os
import matplotlib.pyplot as plt
from control.matlab import * 
import numpy as np
import pygad

def pidtest(solution, solution_idx):
    s = tf([1, 0], 1)
    dt = 1
    G = tf(.325,[350, 1])
    K = solution[0] + solution[1]/s + solution[2]*s/(1+0.001*s)
    Loop = series(K,G)
    ClosedLoop = feedback(Loop,1)
    y,t = step(ClosedLoop,np.arange(0,1800,dt))

    # overst = (np.max(y)-y[-1])/y[-1]
    
    #CTRLtf = K/(1+K*G)
    u = lsim(K,1-y,t)[0]
    
    Q = 1
    R = 0.001
    J = 1/(dt*np.sum(np.power(Q*(1-y.reshape(-1)),2) + R * np.power(u.reshape(-1),2)))
    #print("###")
    #print(solution)
    #print(J)
    
    return J

def pid(solution):
    s = tf([1, 0], 1)
    dt = 1
    G = tf(.325,[350, 1])
    K = solution[0] + solution[1]/s + solution[2]*s/(1+0.001*s)
    print(K)
    Loop = series(K,G)
    ClosedLoop = feedback(Loop,1)
    t = np.arange(0,1800,dt)
    y,t = step(ClosedLoop,t)

    u = lsim(K,1-y,t)[0]
    
    Q = 1
    R = 0.001
    J = 1/(dt*np.sum(np.power(Q*(1-y.reshape(-1)),2) + R * np.power(u.reshape(-1),2)))
    print(1/J)

    yout, t_ = step(ClosedLoop,t)
    plt.figure(3)
    plt.subplot(2,1,1)
    plt.plot(t_, u,'r')
    plt.subplot(2,1,2)
    plt.plot(t_, yout)
    plt.show()

def callback_gen(ga_instance):
    if ga_instance.generations_completed%10 == 0:
      print("Generation : ", ga_instance.generations_completed)
      print("Fitness of the best solution :", ga_instance.best_solution()[1])

###########################
num = .325
den = [350, 1]
dt = 1
planta = tf(num, den)
print(planta)
# Resp del sistema a escalon
plt.figure(1)
yout, t = step(planta,np.arange(0,1800,dt))
print(len(yout))
plt.plot(t, yout)
###########################

fitness_function = pidtest

num_generations = 100
PopSize = 25
num_genes = 3
num_parents_mating = round(PopSize/2)

# Seleccion de padres Stochastic uniform
parent_selection_type = "sus"
# Padres a mantener
keep_parents = round(0.8*num_parents_mating)
# individuos garantizados a sobrevivir
keep_elitism = round(0.05*PopSize)
# cruce
crossover_type = "scattered"
# mutacion                         gene_space = {'low': 0, 'high': 500},
mutation_type = "random"
#mutation_by_replacement=True

ga_instance = pygad.GA(num_generations=num_generations,
                       num_parents_mating=num_parents_mating,
                       fitness_func=fitness_function,
                       sol_per_pop=PopSize,
                       num_genes=num_genes,
                       parent_selection_type=parent_selection_type,
                       keep_parents=keep_parents,
                       keep_elitism=keep_elitism,
                       crossover_type=crossover_type,
                       mutation_type=mutation_type,
                       init_range_low=0.0,
                       init_range_high=0.0)
#                       callback_generation=callback_gen)

ga_instance.run()
#ga_instance = pygad.load("PID_AG_58.3")

solution, solution_fitness, solution_idx = ga_instance.best_solution()
print("Parametetros de la mejor solucion : {solution}".format(solution=solution))
print("Valor de desmpeño de la mejor solucion = {solution_fitness}".format(solution_fitness=1/solution_fitness))

#ga_instance.save("PID_AG_09")

ga_instance.plot_fitness()
#solution = [19.69376155, 0.09487479, -0.02337229]

# Probar solucion
pid(solution)


###############################################################
###
###  Identificacion con modelo ARX utilizando una arquitectura 
###   de red de perceptron multicapa (MLP) implementada en Keras
###
###############################################################

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy import linalg as LA
from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LeakyReLU
from keras.callbacks import ModelCheckpoint

###############################################################

model_salvado = 'RN_entrenadas/ident_arx_mlp_8-4-2-1_LR-R_sc_v1.h5'
model_cargar = 'RN_entrenadas/ident_arx_mlp_8-4-2-1_LR-R_sc_v1.h5'

temper = 'temp_s'
url = '/home/USER/Documentos/PG/Python/Calefactor/Adquisicion/'
nombreE = "step_py_6h_s_sp_10a_scaladoN.csv"                # Entrenamiento
nombreV = "step_py_6h_s_sp_9_scaladoN.csv"                  # Validacion
nombreP = "step_py_6h_s_sp_11_scaladoN.csv"                 # Prueba


############################################################

###############################################################################
#       Esta función da formato a los datos de entrada y salida (ARX)
#           |u1 u2 ... up    y1 y2 ... yp   |       |yp+1|
#       X = |u2 u3 ... up+1  y2 y3 ... yp+1 |   y = |yp+2|
#           |...                            |       |    |
#           |...                            |       |... |
#                (tam(input_seq)-p)x(2*p)       (tam(input_seq)-p)x1  
###############################################################################
def form_data(input_sec, output_sec,past):
    data_len=np.max(input_sec.shape)
    X=np.zeros(shape=(data_len-past,2*past))
    Y=np.zeros(shape=(data_len-past,))
    for i in range(0,data_len-past):
        X[i,0:past]=input_sec[i:i+past,0]
        X[i,past:]=output_sec[i:i+past,0]
        Y[i]=output_sec[i+past,0]
    return X,Y

##############################################################################

###############################################################################
#                  Data de entranamiento
###############################################################################
# scale values to 0 to 1 for the ANN to work well
# cargar datos y analizar en columnas
data = pd.read_csv(url+nombreE)

u = data['clft']
y = data[temper]
past = 4

in_train = np.array([u])    # forma: (1,tam(u))
in_train = in_train.T       # forma: (tam(u),1)

out_train = np.array([y])  # forma: (1,tam(y))
out_train = out_train.T     # forma: (tam(y),1)

X_train,Y_train= form_data(in_train, out_train, past) # forma: (tam(u)-2, 4) , (tam(y)-2, 4)
print("Data de entranamiento...OK")
###############################################################################
#                  Data de validacion
###############################################################################

data = pd.read_csv(url+nombreV)
u = data['clft']
y = data[temper]

in_valid = np.array([u])    # forma: (tam(u),1)
in_valid = in_valid.T       # forma: (tam(u),1)

out_valid = np.array([y])   # forma: (1,tam(y))
out_valid = out_valid.T     # forma: (tam(y),1)

X_valid,Y_valid= form_data(in_valid, out_valid, past) # forma: (tam(u)-2, 4) , (tam(y)-2, 4)
print("Data de validacion...OK")
###############################################################################
#                  Data de test
###############################################################################

data = pd.read_csv(url+nombreP)

u = data['clft']
y = data[temper]

in_test = np.array([u])     # forma: (1,tam(y))
in_test = in_test.T         # forma: (tam(u),1)

out_test = np.array([y])    # forma: (1,tam(y))
out_test = out_test.T       # forma: (tam(y),1)

X_test,Y_test= form_data(in_test, out_test, past) # forma: (tam(u)-2, 4) , (tam(y)-2,)
print("Data de test...OK")
###############################################################################
#                        RNA
#  batch_size: numero de muestras que se propagaran/retropropagaran a traves de la red
#  batch size = 1: n de muestras : mejor estimación del gradiente vs mayor coste computacional
#  batch size > 1: < n de muestras : peor estimación del gradiente vs menor coste computacional
#  se requieren (n muestras)/batch size iteraciones para completar 1 epoch
###############################################################################LeakyReLU(alpha=0.05)

model = Sequential()        # serie de capas de neuronas secuenciales
intz = keras.initializers.HeNormal()
model.add(Dense(4, kernel_initializer=intz, activation=LeakyReLU(alpha=0.08), input_dim=2*past))
model.add(Dense(2, kernel_initializer=intz, activation='relu'))
#model.add(Dense(4, activation='relu'))
model.add(Dense(1))

optimizer = keras.optimizers.Adam()
#model = keras.models.load_model(model_cargar)
model.compile(optimizer=optimizer, loss='mse')
########################
checkpoint = ModelCheckpoint(model_salvado, monitor="loss", verbose=1, save_best_only=True, mode="min")
callbacks_list = [checkpoint]

history=model.fit(X_train, Y_train, epochs=50, batch_size=10, callbacks=callbacks_list, 
                                                validation_data=(X_valid,Y_valid), verbose=2, shuffle=True)
model.summary()

############################################################
# Evaluate the model on the test data using `evaluate`
print("Evaluate on test data")
results = model.evaluate(X_test, Y_test, batch_size=128)
print("test loss, test acc:", results)

###############################################################################
#  utilizar los datos de prueba para investigar el rendimiento de la predicción
###############################################################################
prediccion_RNA = model.predict(X_test)


# Guardar el modelo RNA
model.save(model_salvado)

# Cargar modelo desde archivo
model_recargado = keras.models.load_model(model_salvado)

# Verificar  el estado esté preservado
prediccion_nueva = model_recargado.predict(X_test)
print("Diferencia entre modelo guardado y cargado:")
print(np.testing.assert_allclose(prediccion_RNA, prediccion_nueva, rtol=1e-6, atol=1e-6))

# ploteo
plt.figure()
plt.plot(Y_test, 'b', label='Salida real')
plt.plot(prediccion_RNA,'r--', label='Salida predicha')
#plt.plot(prdcc,'k', label='Salida predicha FOR')
plt.xlabel('Tiempo discreto')
plt.ylabel('Salida')
plt.grid()
plt.legend()
#plt.show()

###############################################################################
#       graficar entrenamiento y validación
###############################################################################

loss=history.history['loss']
val_loss=history.history['val_loss']
epochs=range(1,len(loss)+1)
plt.figure()
plt.plot(epochs, loss,'b', label='funcion perdida de entrenamiento')
plt.plot(epochs, val_loss,'r', label='Validacion de la funcion perdida')
plt.title('Entrenamiento y validacion de la funcion de perdida')
plt.xlabel('Entrenamientos')
plt.ylabel('Funcion de perdida')
plt.xscale('log')
#plt.yscale('log')
plt.legend()
plt.grid()
plt.show()

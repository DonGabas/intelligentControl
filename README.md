# Intelligent control techniques

Three intelligent control techniques, a controller based on neural networks in an internal model control (IMC) structure, a fuzzy controller (FLC) and the tuning of a PID controller using genetic algorithm (AG).

## Process

The process under control is a temperature control device (based on the device https://apmonitor.com/pdc/index.php/Main/ArduinoTemperatureControl) implemented as a single-input single-output (SISO) system. The Arduino board and Python library code used for the implementation is a modification of the code developed by apmonitor for the TcLab.

## Neural networks

Two neural networks are employed: one that emulates the dynamics of the process and another that emulates the inverse dynamics. These networks were trained using the Keras-TensorFlow framework, and the training process was conducted offline.

## Fuzzy control

The fuzzy controller utilizes linguistic variables such as error, rate of change of error, and duty cycle. The error variable is defined by four linguistic terms, the rate of change is defined by three linguistic terms, and the duty cycle is defined by three linguistic terms. A total of twelve control rules are established using Mamdani's method of inference, and centroid defuzzification is used for output aggregation.

## Genetic algorithm

The genetic algorithm is employed for the tuning of a PID controller using a fitness function based on the quadratic objective function of the linear quadratic regulator (LQR). The evolution process involves 25 individuals, selected through stochastic universal selection with a 5% elitism rate. The reproduction includes scattered crossing, and a 1% mutation rate is applied.

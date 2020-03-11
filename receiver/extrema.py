import numpy as np
import matplotlib.pyplot as plt

x = np.linspace (0, 50, 1000)
y = 0.75 * np.sin(x)

peaks = np.where((y[1:-1] > y[0:-2]) * (y[1:-1] > y[2:]))[0] + 1
dips = np.where((y[1:-1] < y[0:-2]) * (y[1:-1] < y[2:]))[0] + 1

# The above makes a list of all indices where the value of y[i] is greater than both of its neighbours
# It does not check the endpoints, which only have one neighbour each
# The extra +1 at the end is necessary because where finds the indices within the slice y[1:-1],
# not the full array y. The [0] is necessary because where returns a tuple of arrays, where the first element 
# is the array we want.

plt.plot (x, y)
plt.plot (x[peaks], y[peaks], 'o')
plt.plot (x[dips], y[dips], 'o')

plt.show()
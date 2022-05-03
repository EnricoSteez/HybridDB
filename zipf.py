from scipy.stats import zipfian
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(1, 1)
N = 1e5
x = np.arange(1, N, 100)
colors = ["r", "g", "b", "c", "m", "y", "b"]
for a in range(0, 6):
    ax.plot(
        x,
        zipfian.pmf(x, a + 1, N),
        ".-" + colors[a],
        linewidth="0.7",
        markersize="3",
        label=f"a={a+1}",
    )
ax.set_xscale("log")
ax.set_yscale("log")
ax.legend(loc="best", frameon=False)
# ax.vlines(x, 0, zipfian.pmf(x, a=3, n=N), colors="b", lw=1, alpha=0.5)
plt.show()

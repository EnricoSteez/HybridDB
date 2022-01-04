#%%
from numpy import random
import matplotlib.pyplot as plt
from numpy.random.mtrand import seed
import seaborn as sns

sns.displot(
    random.poisson(
        lam=10,
        size=100,
    ),
    kind="kde",
)

plt.show()

# %%

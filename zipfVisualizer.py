#%%
from numpy import random
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

zipf = random.zipf(a=1.7, size=1000)

exp = random.exponential(scale=100, size=1000)

unif = random.uniform(low=1, high=100, size=1000)

# %%
data = {"ZIPF": zipf, "EXP": exp, "UNIF": unif}
df = pd.DataFrame(data=data)

df.to_excel("/Users/enrico/Desktop/Book1.xlsx", index=False)
# with pd.ExcelWriter("/Users/enrico/Desktop/Book1.xlsx")
#%%
sns.displot(unif[unif < 100], kde=False)
plt.show()

#%%
# sns.displot(zipf[zipf < 100], kde=False)
# plt.show()
zipf = random.zipf(a=1.7, size=1000)
print(max(zipf))

#%%
sns.displot(exp[exp < 100], kde=False)
plt.show()

# %%

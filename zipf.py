from scipy.stats import zipfian
import telegram
import json
import sys
from os import path

# import matplotlib.pyplot as plt
# import numpy as np


def notify(message):
    with open("./keys/keys.json", "r") as keys_file:
        k = json.load(keys_file)
        token = k["telegram_token"]
        chat_id = k["telegram_chat_id"]
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)


def main(N: int, a: int):
    notify(f"Beginning zipfian N={N} a={a}")
    with open(f"zipfian/{N}_{a}", "w") as file:
        for i in range(1, N + 1):
            n = zipfian.pmf(i, a, N)
            file.write(f"{n}\n")
        # file.truncate(file.tell() - 1)
    notify(f"Finished zipfian N={N} a={a}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 {path.basename(__file__)} N a")
        sys.exit(1)

    N = int(sys.argv[1])
    a = int(sys.argv[2])

    main(N, a)

# fig, ax = plt.subplots(1, 1)
# N = 1e5
# x = np.arange(1, N, 100)
# colors = ["r", "g", "b", "c", "m", "y", "b"]
# for a in range(0, 6):
#     ax.plot(
#         x,
#         zipfian.pmf(x, a + 1, N),
#         ".-" + colors[a],
#         linewidth="0.7",
#         markersize="3",
#         label=f"a={a+1}",
#     )
# ax.set_xscale("log")
# ax.set_yscale("log")
# ax.legend(loc="best", frameon=False)
# # ax.vlines(x, 0, zipfian.pmf(x, a=3, n=N), colors="b", lw=1, alpha=0.5)
# plt.show()

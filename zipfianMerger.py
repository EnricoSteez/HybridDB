def mergeZipfians(
    n1: int,
    skew1: float,
    tot_tp_1: float,
    read_percent_1: float,
    size1: float,
    n2: int,
    skew2: float,
    tot_tp_2: float,
    read_percent_2: float,
    size2: float,
) -> tuple[list[float], list[float], list[float]]:
    s = [size1] * n1 + [size2] * n2
    t_r = [0.1]
    t_r.clear()
    t_w = [0.1]
    t_w.clear()


    with open(f"zipfian/{n1}_{int(skew1)}", "r") as file:
        for _ in range(n1):
            prob = float(file.readline().split()[0]) / 2
            t_r.append(prob * tot_tp_1 * read_percent_1)
            t_w.append(prob * tot_tp_1 * (1 - read_percent_1))
    with open(f"zipfian/{n2}_{int(skew2)}", "r") as file:
        for _ in range(n2):
            prob = float(file.readline().split()[0]) / 2
            t_r.append(prob * tot_tp_2 * read_percent_2)
            t_w.append(prob * tot_tp_2 * (1 - read_percent_2))

    print(
        f"Number of items: {len(s)}, max_size={max(s)}MB, min_size={min(s)}MB\n"
        f" Two Zipfian distributions, skew1={skew1}\n skew2={skew2}\n"
        f"throughputs read: max={max(t_r):.2e}, min={min(t_r):.2e}\n"
        f"throughputs write: max={max(t_w):.2e}, min={min(t_w):.2e}\n"
    )
    return (s, t_r, t_w)

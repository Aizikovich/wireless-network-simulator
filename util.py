from enum import Enum
import math
import environment
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np


class EnvType(Enum):
    RURAL = 0
    SUBURBAN = 1
    URBAN = 2


MIN_RSRP = -120  # -140 #dB


def compute_rsrp(ue, bs, env):
    if bs.bs_type == "sat":
        return bs.sat_eirp - bs.path_loss - bs.atm_loss - bs.ut_G_T
    elif bs.bs_type == "drone_relay":
        return bs.compute_rsrp_drone(ue)
    else:
        # lte and nr case
        path_loss = compute_path_loss_cost_hata(ue, bs, env)
        subcarrier_power = 0
        if (bs.bs_type == "lte"):
            subcarrier_power = 10 * math.log10(bs.antenna_power * 1000 / ((bs.total_prb / 10) * bs.number_subcarriers))
        else:
            subcarrier_power = 10 * math.log10(
                bs.antenna_power * 1000 / ((bs.total_prb / (10 * 2 ** bs.numerology)) * bs.number_subcarriers))
        return subcarrier_power + bs.antenna_gain - bs.feeder_loss - path_loss


def compute_path_loss_cost_hata(ue, bs, env, save=None):
    # compute distance first
    dist = math.sqrt((ue.current_position[0] - bs.position[0]) ** 2 + (ue.current_position[1] - bs.position[1]) ** 2 + (
                ue.h_m - bs.h_b) ** 2)
    if dist == 0:  # just to avoid log(0) in path loss computing
        dist = 0.01
    # compute C_0, C_f, b(h_b), a(h_m) and C_m with the magic numbers defined by the model
    if bs.carrier_frequency <= 1500 and bs.carrier_frequency >= 150:
        C_0 = 69.55
        C_f = 26.16
        b = 13.82 * math.log10(bs.h_b)
        if env.env_type == EnvType.URBAN:
            C_m = 0
        elif env.env_type == EnvType.SUBURBAN:
            C_m = -2 * ((math.log10(bs.carrier_frequency / 28)) ** 2) - 5.4
        else:
            C_m = -4.78 * ((math.log10(bs.carrier_frequency)) ** 2) + 18.33 * math.log10(bs.carrier_frequency) - 40.94
    else:
        C_0 = 46.3
        C_f = 26.16
        b = 13.82 * math.log10(bs.h_b)
        if env.env_type == EnvType.URBAN:
            C_m = 3
        elif env.env_type == EnvType.SUBURBAN:
            C_m = 0
        else:
            raise Exception("COST-HATA model is not defined for frequencies in 1500-2000MHz with RURAL environments")

    if env.env_type == EnvType.SUBURBAN or env.env_type == EnvType.RURAL:
        a = (1.1 * math.log10(bs.carrier_frequency) - 0.7) * ue.h_m - 1.56 * math.log10(bs.carrier_frequency) + 0.8
    else:
        if bs.carrier_frequency >= 150 and bs.carrier_frequency <= 300:
            a = 8.29 * (math.log10(1.54 * ue.h_m) ** 2) - 1.1
        else:
            a = 3.2 * (math.log10(11.75 * ue.h_m) ** 2) - 4.97

    path_loss = C_0 + C_f * math.log10(bs.carrier_frequency) - b - a + (44.9 - 6.55 * math.log10(bs.h_b)) * math.log10(
        dist / 1000) + C_m
    if (save is not None):
        save = path_loss
    return path_loss


def find_bs_by_id(bs_id):
    return environment.wireless_environment.bs_list[bs_id]


def find_ue_by_id(ue_id):
    return environment.wireless_environment.ue_list[ue_id]


run = 0


def plot(ue, bs, env):
    global ax
    global fig
    global run
    if run == 0:
        plt.ion()
        fig, ax = plt.subplots()
        run = 1

    x_ue = []
    y_ue = []
    x_bs = []
    y_bs = []

    plt.cla()

    # ax.set_xlim(0, env.x_limit)
    # ax.set_ylim(0, env.y_limit)

    colors = cm.rainbow(np.linspace(0, 1, len(bs)))

    for j in bs:
        x_bs.append(find_bs_by_id(j).position[0])
        y_bs.append(find_bs_by_id(j).position[1])

    for i in range(0, len(ue)):
        x_ue.append(find_ue_by_id(ue[i]).current_position[0])
        y_ue.append(find_ue_by_id(ue[i]).current_position[1])

    for i in range(0, len(ue)):
        for j in range(0, len(bs)):
            if find_ue_by_id(ue[i]).current_bs == j:
                ax.scatter(x_ue[i], y_ue[i], color=colors[j])
                break
        else:
            ax.scatter(x_ue[i], y_ue[i], color="tab:grey")

    for i in range(0, len(ue)):
        ax.annotate(str(ue[i]), (x_ue[i], y_ue[i]))

    for j in range(0, len(bs)):
        if find_bs_by_id(j).bs_type == "drone_relay":
            ax.scatter(x_bs[j], y_bs[j], color=colors[j], label="BS", marker="^", s=400,
                       edgecolor=colors[find_bs_by_id(j).linked_bs], linewidth=3)
        elif find_bs_by_id(j).bs_type == "drone_bs":
            ax.scatter(x_bs[j], y_bs[j], color=colors[j], label="BS", marker="^", s=400)
        else:
            ax.scatter(x_bs[j], y_bs[j], color=colors[j], label="BS", marker="s", s=400)

    for j in range(0, len(bs)):
        ax.annotate("BS" + str(j), (x_bs[j], y_bs[j]))

    ax.grid(True)
    ax.set_ylabel("[m]")
    ax.set_xlabel("[m]")
    fig.canvas.draw()


def plot_network_topology(use, bss, title="Network Topology"):
    # Plot the network topology
    fig, ax = plt.subplots()
    x = []
    y = []
    x1 = []
    y1 = []

    colors = cm.rainbow(np.linspace(0, 1, len(bss)))
    for j in bss:
        x.append(find_bs_by_id(j).position[0])
        y.append(find_bs_by_id(j).position[1])
    for j in range(0, len(bss)):
        ax.scatter(x[j], y[j], color=colors[j], label="BS", marker="s", s=400)

    for j in range(0, len(bss)):
        ax.annotate("BS" + str(j), (x[j], y[j]))

    for i in range(0, len(use)):
        x1.append(find_ue_by_id(use[i]).current_position[0])
        y1.append(find_ue_by_id(use[i]).current_position[1])

    for i in range(0, len(use)):
        ax.scatter(x1[i], y1[i], color="tab:grey")

    for i in range(0, len(use)):
        ax.annotate("UE" + str(i), (x1[i], y1[i]))


    plt.title(title)
    ax.grid(True)
    ax.set_ylabel("[m]")
    ax.set_xlabel("[m]")
    fig.canvas.draw()
    plt.show()


def handel_ts_control_msg(ue_ids, bss, msg, env):
    """
    This function handles the Traffic Steering control message from ts in the RIC
    [INFO] HandOff request is {
                    "command": "HandOff",
                    "seqNo": 1,
                    "ue": "UE1",
                    "fromCell": "BS1",
                    "toCell": "BS2",
                    "timestamp": "Thu Nov 30 09:39:55 2023",
                    "reason": "HandOff Control Request from TS xApp",
                    "ttl": 10
                }
    :param ue_ids: list of ue ids
    :param bss: list of bs ids
    :param msg: JSON message from ts
    :param env: environment

    """
    try:
        ue_id = msg["ue"]
        from_cell = msg["fromCell"]
        to_cell_id = msg["toCell"]
        to_cell = find_bs_by_id(to_cell_id)
        ue = find_ue_by_id(ue_id)
        ue.connected_bs = to_cell
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        print(f"[INFO] successfully handed off UE {ue_id} from {from_cell} to {to_cell_id}")


























import environment
import util
import random
import time
import os
import pandas as pd
import json
import api
from flask import Flask, request
from threading import Thread
from queue import Queue

app = Flask(__name__)


def run_simulator(ts_queue=None):
    N_UE = 20
    ITER = 4000
    random.seed(2)

    def init_bs(bs):
        return env.place_NR_base_station(bs["pos"], bs["freq"], bs["numerology"], bs["power"],
                                         bs["gain"], bs["loss"], bs["bandwidth"],
                                         total_bitrate=bs["max_bitrate"])

    with open('bs_config.json', 'r') as f:
        config = json.load(f)
    parm = config['parm']

    env = environment.wireless_environment(4000, sampling_time=0.001)
    ues = []
    bss = []
    error = []
    latency = {}
    prbs = {}
    bitrates = {}
    # insert UEs
    for i in range(0, N_UE):
        id = env.insert_ue(0, starting_position=(
            random.randint(0, env.x_limit - 1), random.randint(0, env.y_limit - 1), 1),
                           speed=1000, direction=random.randint(0, 359))
        ues.append(id)

    # insert BSs
    nr_bs2 = env.place_NR_base_station((1500, 1500, 40), 800, 2, 20, 16, 3, 100, total_bitrate=10000)
    bss.append(nr_bs2)
    for bs in parm:
        bss.append(init_bs(bs))

    env.initial_timestep()
    print(env.wardrop_beta)

    util.plot_network_topology(ues, bss)

    for ue_id in ues:
        ue = util.find_ue_by_id(ue_id)
        ue.connect_to_bs_random()
        print(f"UE{ue_id} | current_bs: {util.find_ue_by_id(ue_id).current_bs} ")

    env.next_timestep()
    print(util.find_ue_by_id(ues[1]).current_bs)

    for i in range(ITER):
        if i % 1000 == 0:
            util.plot_network_topology(ues, bss, f"Network topology step {i}")
        if i % 100 == 0:
            print("-------------------", i, "-------------------")
            # if i != 0:
            #     for elem in ues:
            #         phonex = util.find_ue_by_id(elem)
            #         for bsx in phonex.current_bs:
            #             if phonex.current_bs[bsx] < phonex.bs_bitrate_allocation[bsx]:
            #                 print("Warning: UE", elem, "has saturated BS ", bsx)

            for bsi in bss:
                if util.find_bs_by_id(bsi).bs_type != "sat":
                    print("BS ", bsi, " PRB: ", util.find_bs_by_id(bsi).allocated_prb, "/",
                          util.find_bs_by_id(bsi).total_prb, " Bitrate: ", util.find_bs_by_id(bsi).allocated_bitrate,
                          "/",
                          util.find_bs_by_id(bsi).total_bitrate)
                else:
                    print("BS ", bsi, " PRB: ", util.find_bs_by_id(bsi).frame_utilization / 64, "/",
                          util.find_bs_by_id(bsi).total_symbols / 64, " Bitrate: ",
                          util.find_bs_by_id(bsi).allocated_bitrate, "/", util.find_bs_by_id(bsi).total_bitrate)
        max_e = 0
        for phone in ues:
            # print(phone)
            util.find_ue_by_id(phone).update_connection()
            # phone2.update_connection()
            l_max = 0
            l_min = float("inf")
            latency_phone = {}
            for bsa in util.find_ue_by_id(phone).bs_bitrate_allocation:
                l = util.find_bs_by_id(bsa).compute_latency(phone)

                latency_phone[bsa] = l

                if util.find_ue_by_id(phone).bs_bitrate_allocation[bsa] > 0.0001 and l > l_max:
                    l_max = l
                elif util.find_ue_by_id(phone).bs_bitrate_allocation[bsa] < util.find_bs_by_id(bsa).total_bitrate - (
                        env.wardrop_epsilon / (2 * env.wardrop_beta)) and l < l_min:
                    l_min = l
            e = l_max - l_min
            if e > max_e:
                max_e = e
            if phone not in latency:
                latency[phone] = []
            latency[phone].append(latency_phone)
        error.append(max_e)
        for bsi in bss:
            if bsi not in prbs:
                prbs[bsi] = []
            if bsi not in bitrates:
                bitrates[bsi] = []
            if util.find_bs_by_id(bsi).bs_type != "sat":
                prbs[bsi].append(util.find_bs_by_id(bsi).allocated_prb)
                bitrates[bsi].append(util.find_bs_by_id(bsi).allocated_bitrate)
            else:
                prbs[bsi].append(util.find_bs_by_id(bsi).frame_utilization / 64)
                bitrates[bsi].append(util.find_bs_by_id(bsi).allocated_bitrate)

        ue_data = api.report_ues_msr(ues, bss, env)
        cell_data = api.report_cell_msr(ues, bss, env)

        if ts_queue is not None:
            control_msg = ts_queue.get()
            util.handel_ts_control_msg(ues, bss, control_msg, env)

        env.next_timestep()


def latency_calculation(latency, error, prbs, bitrates, bss):
    ue_latency = {}
    for phone in latency:
        df = pd.DataFrame.from_dict(latency[phone])
        df.to_csv(".\\data\\latency_UE" + str(phone) + ".csv", sep=";")

    df = pd.DataFrame(error)
    df.to_csv(".\\data\\error.csv", sep=";")

    for bsi in bss:
        df = pd.DataFrame.from_dict(prbs[bsi])
        df.to_csv(".\\data\\resourceblocks_BS" + str(bsi) + ".csv", sep=";")
        df = pd.DataFrame.from_dict(bitrates[bsi])
        df.to_csv(".\\data\\bitrate_BS" + str(bsi) + ".csv", sep=";")


@app.route('/api/echo', methods=['POST'])
def receive():
    try:
        received_data = request.json
        if received_data is not None:
            print("OK \nTS Request:")
            print(received_data)
            received_data = None
        else:
            print("No UE data received", flush=True)
            time.sleep(1)
        return "UE Data received successfully!"

    except Exception as e:
        print("Error:", e, flush=True)
        return "Error occurred while receiving UE data"


if __name__ == "__main__":
    run_simulator()
    ts_msgs_queue = Queue()
    ts_thread = Thread(target=latency_calculation, args=(ts_msgs_queue,))
    ts_thread.daemon = True
    ts_thread.start()
    app.run(host='0.0.0.0', port=80)

import json
import random

import requests
from util import find_ue_by_id, find_bs_by_id
import datetime


def report_ues_msr(ue_id_list, bslist, env):
    data = []

    for ue_id in ue_id_list:
        ue_report = {
            "DRB.UEThpDl": random.uniform(1.0, 100.0),
            "RF.serving.RSRP": random.uniform(1.0, 100.0),
            "RF.serving.RSRQ": 'x',
            "RF.serving.RSSINR": random.uniform(1.0, 100.0),
            "RRU.PrbUsedDl": random.uniform(1.0, 100.0),
            "Viavi.UE.anomalies": random.randint(0, 1),
            "du-id": 1001,
            "measTimeStampRf": f"{datetime.datetime.now()}",
            "nbCellIdentity_0": None,
            "nbCellIdentity_1": None,
            "nbCellIdentity_2": None,
            "nbCellIdentity_3": None,
            "nbCellIdentity_4": None,
            "nrCellIdentity": None,
            "rsrp_nb0": random.uniform(1.0, 100.0),
            "rsrp_nb1": random.uniform(1.0, 100.0),
            "rsrp_nb2": random.uniform(1.0, 100.0),
            "rsrp_nb3": random.uniform(1.0, 100.0),
            "rsrp_nb4": random.uniform(1.0, 100.0),
            "rsrq_nb0": 'x',  # 'x' means 'not available'
            "rsrq_nb1": 'x',
            "rsrq_nb2": 'x',
            "rsrq_nb3": 'x',
            "rsrq_nb4": 'x',
            "rssinr_nb0": random.uniform(1.0, 100.0),
            "rssinr_nb1": random.uniform(1.0, 100.0),
            "rssinr_nb2": random.uniform(1.0, 100.0),
            "rssinr_nb3": random.uniform(1.0, 100.0),
            "rssinr_nb4": random.uniform(1.0, 100.0),
            "targetTput": random.uniform(1.0, 100.0),
            "ue-id": f'UE{ue_id}',
            "x": 0.0,
            "y": 0.0
        }

        ue = find_ue_by_id(ue_id)
        x, y = ue.current_position
        ue_report["x"] = x
        ue_report["y"] = y
        serving_bs = list(ue.current_bs.keys())[0]
        ue_report["nrCellIdentity"] = serving_bs
        ue_thp =  ue.current_bs[serving_bs]
        ue_report["DRB.UEThpDl"] = ue_thp
        bss_rsrp = env.discover_bs(ue_id)
        serving_rsrp = bss_rsrp[serving_bs]
        serving_sinr = find_bs_by_id(serving_bs).compute_sinr(bss_rsrp)
        ue_report["RF.serving.RSRP"] = serving_rsrp
        ue_report["RF.serving.RSSINR"] = serving_sinr
        nb_bs = list(bss_rsrp.keys())
        nb_bs.remove(serving_bs)
        # for every neighbor base station
        for bn_bs_id in nb_bs:
            ue_report[f"nbCellIdentity_{nb_bs.index(bn_bs_id)}"] = bn_bs_id
            curr_bs = find_bs_by_id(bn_bs_id)
            rsrp = bss_rsrp[bn_bs_id]
            sinr = curr_bs.compute_sinr(env.discover_bs(ue_id))
            ue_report[f"rsrp_nb{nb_bs.index(bn_bs_id)}"] = rsrp
            ue_report[f"rssinr_nb{nb_bs.index(bn_bs_id)}"] = sinr
            # print(f"rsrp: {rsrp}, sinr: {sinr}")
            # TODO: see if isolation forest can handle this


        data.append(ue_report)
        print(f"\n\n example ue data: {data[0]} \n\n")
    ue_data = json.dumps(data)
    try:
        response = requests.post('http://127.0.0.1:5001/receive_ue', json=json.loads(ue_data))
        return response
    except Exception as e:
        print(f"Error While sending cell data:\n{e}")
    return None





def report_cell_msr(ue_id_list, bslist, env):
    """

    """
    jsons = []
    for bs_id in bslist:
        current_bs = find_bs_by_id(bs_id)
        actual_bitrate = current_bs.allocated_bitrate
        measurements = {
            "du-id": 1001,
            "measTimeStampRf": f"{datetime.datetime.now()}",
            "nrCellIdentity": f'{bs_id}',
            "throughput": actual_bitrate,
            "x": current_bs.position[0],
            "y": current_bs.position[1],
            ### TODO: check these values
            "availPrbDl": random.randint(1, 100),
            "availPrbUl": random.randint(1, 100),
            "measPeriodPrb": current_bs.allocated_prb,
            ### TODO: check these values
            "pdcpBytesUl": actual_bitrate,
            "pdcpBytesDl": actual_bitrate,
            "measPeriodPdcpBytes": random.randint(1, 100),
        }
        jsons.append(measurements)
    print(f"\n\n example cell data: {jsons[0]} \n\n")
    cell_data = json.dumps(jsons)
    try:
        response = requests.post('http://127.0.0.1:5000/receive_cell', json=json.loads(cell_data))
        return response
    except Exception as e:
        print(f"Error While sending cell data:\n{e}")
    return None


def send_msr_to_server(jsons, url):
    for data in jsons:
        requests.post(url, json=json)
        print(f"sent {data} to {url}")

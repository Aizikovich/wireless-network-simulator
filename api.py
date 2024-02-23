import json
import random

import requests
from util import find_ue_by_id
import datetime


def report_ues_msr(ue_id_list, bslist, env):
    """
    send post request to the server to with the UE's measurements json, following format:

        fieldKey           fieldType
    --------           ---------
    DRB.UEThpDl        float
    RF.serving.RSRP    float
    RF.serving.RSRQ    float
    RF.serving.RSSINR  float
    RRU.PrbUsedDl      float
    Viavi.UE.anomalies integer
    du-id              integer
    measTimeStampRf    string
    nbCellIdentity_0   string
    nbCellIdentity_1   string
    nbCellIdentity_2   string
    nbCellIdentity_3   string
    nbCellIdentity_4   string
    nrCellIdentity     string
    rsrp_nb0           float
    rsrp_nb1           float
    rsrp_nb2           float
    rsrp_nb3           float
    rsrp_nb4           float
    rsrq_nb0           float
    rsrq_nb1           float
    rsrq_nb2           float
    rsrq_nb3           float
    rsrq_nb4           float
    rssinr_nb0         float
    rssinr_nb1         float
    rssinr_nb2         float
    rssinr_nb3         float
    rssinr_nb4         float
    targetTput         float
    ue-id              string
    x                  float
    y                  float
    """
    # data = []
    # for id in ue_id_list:
    #     ue = find_ue_by_id(id)
    #
    #     # serving cell
    #     nrCellIdentity = list(ue.current_bs.keys())[0]
    #     thp = ue.current_bs[nrCellIdentity]
    #     print(f"serving cell: {nrCellIdentity}")
    #     print(f"thp: {thp}")
    #     # neighbor cells
    #     nb_cells = list(env.discover_bs(id).keys())
    #     print(f"nb_cells: {nb_cells}")
    #     rsrp = [env.discover_bs(id)[cell] for cell in nb_cells]
    #
    #     if len(rsrp) < 5:
    #         rsrp += [0] * (5 - len(rsrp))
    #         nb_cells += [''] * (5 - len(nb_cells))

    ue_data_list = []
    for i in range(1, 7):
        ue = {
            "DRB.UEThpDl": random.uniform(1.0, 100.0),
            "RF.serving.RSRP": random.uniform(1.0, 100.0),
            "RF.serving.RSRQ": random.uniform(1.0, 100.0),
            "RF.serving.RSSINR": random.uniform(1.0, 100.0),
            "RRU.PrbUsedDl": random.uniform(1.0, 100.0),
            "Viavi.UE.anomalies": random.randint(0, 1),
            "du-id": 1001,
            "measTimeStampRf": f"{datetime.datetime.now()}",
            "nbCellIdentity_0": 'c1/B2',
            "nbCellIdentity_1": 'c1/B13',
            "nbCellIdentity_2": 'c1/B4',
            "nbCellIdentity_3": 'c1/B5',
            "nbCellIdentity_4": 'c1/B6',
            "nrCellIdentity": 'c1/B2',
            "rsrp_nb0": random.uniform(1.0, 100.0),
            "rsrp_nb1": random.uniform(1.0, 100.0),
            "rsrp_nb2": random.uniform(1.0, 100.0),
            "rsrp_nb3": random.uniform(1.0, 100.0),
            "rsrp_nb4": random.uniform(1.0, 100.0),
            "rsrq_nb0": random.uniform(1.0, 100.0),
            "rsrq_nb1": random.uniform(1.0, 100.0),
            "rsrq_nb2": random.uniform(1.0, 100.0),
            "rsrq_nb3": random.uniform(1.0, 100.0),
            "rsrq_nb4": random.uniform(1.0, 100.0),
            "rssinr_nb0": random.uniform(1.0, 100.0),
            "rssinr_nb1": random.uniform(1.0, 100.0),
            "rssinr_nb2": random.uniform(1.0, 100.0),
            "rssinr_nb3": random.uniform(1.0, 100.0),
            "rssinr_nb4": random.uniform(1.0, 100.0),
            "targetTput": random.uniform(1.0, 100.0),
            "ue-id": f'UE{i}',
            "x": 0.0,
            "y": 0.0
        }
        ue_data_list.append(ue)
    ue_data = json.dumps(ue_data_list)
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
    for bs in bslist:
        measurements = {
            "du-id": 1001,
            "measTimeStampRf": f"{datetime.datetime.now()}",
            "nrCellIdentity": 'c1/B2',
            "throughput": random.uniform(1.0, 100.0),
            "x": 0.0,
            "y": 0.0,
            "availPrbDl": random.randint(1, 100),
            "availPrbUl": random.randint(1, 100),
            "measPeriodPrb": random.randint(1, 100),
            "pdcpBytesUl": random.randint(1, 100),
            "pdcpBytesDl": random.randint(1, 100),
            "measPeriodPdcpBytes": random.randint(1, 100),
        }
        jsons.append(measurements)

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

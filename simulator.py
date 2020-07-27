from collections import deque

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math
from conf import Conf
import random_generators as rgs


def init_pd():
    pd.set_option('precision', 3)
    pd.set_option('max_columns', 20)
    pd.set_option('display.expand_frame_repr', False)


def raw_table():
    table = pd.DataFrame(index=list(range(1, Conf.CLIENT_NO + 1)), columns=Conf.TABLE_COLUMNS)
    table.loc[:, 'srv beg'] = 0
    table.loc[1, 'arrival t'] = 0
    btw_arrival = rgs.btw_arrival()
    patience = rgs.queue_time()
    table.loc[:, 'remaining_P'] = patience
    table.loc[:, 'init_patience'] = patience
    table.loc[:, 'corona'] = rgs.corona()
    table.loc[:, 'srv t'] = rgs.service_time()
    btw_arrival[0] = 0
    table.loc[:, 't btw arrival'] = btw_arrival
    table.loc[:, 'arrival t'] = np.cumsum(btw_arrival)
    return table


def get_col_idx(name):
    return Conf.TABLE_COLUMNS.index(name)


def check_patient_is_tired(patient, last_visit_end=None):
    # visiting_srv_end = patient[get_col_idx('srv_end')]
    visiting_srv_end = patient[5]
    if last_visit_end and last_visit_end > visiting_srv_end:
        visit_start = last_visit_end
    else:
        visit_start = visiting_srv_end

    delay = visit_start - visiting_srv_end
    # patient[get_col_idx('remaining_P')] -= delay
    patient[6] -= delay

    # if patient[get_col_idx('remaining_P')] < 0:
    if patient[6] < 0:
        patient[6] = "gone"
        return True
    return False


def pop_tired_patients(corona_queue, normal_queue, last_visit_end):
    go = True
    count=0
    while go:
        go = False

        if len(corona_queue) > 0 and check_patient_is_tired(corona_queue[0], last_visit_end):
            corona_queue.popleft()
            count+=1
            go = True
        if len(normal_queue) > 0 and check_patient_is_tired(normal_queue[0], last_visit_end):
            normal_queue.popleft()
            count+=1
            go = True
    return count

def flush_patients(visit_queues, room_queues_length,
                   visiting_patients, arrive_time=None):
    min_room_length = math.inf
    min_room_length_idx = 0
    for room_idx in range(len(Conf.DOCTORS)):
        while True:
            min_visit_end = 1e20
            min_doctor_idx = 0

            for doc_idx in range(len(Conf.DOCTORS[room_idx])):
                last_visit_end = -1e20
                if visiting_patients[room_idx][doc_idx] is not None:
                    # last_visit_end = visiting_patients[room_idx][doc_idx][get_col_idx("visit end")]
                    last_visit_end = visiting_patients[room_idx][doc_idx][9]
                if arrive_time:
                    if last_visit_end <= arrive_time:
                        if last_visit_end < min_visit_end:
                            min_visit_end = last_visit_end
                            min_doctor_idx = doc_idx
                else:
                    if last_visit_end < min_visit_end:
                        min_visit_end = last_visit_end
                        min_doctor_idx = doc_idx
            if arrive_time and min_visit_end == 1e20:
                break
            if min_visit_end == -1e20:
                min_visit_end = None


            visiting_patients[room_idx][min_doctor_idx] = None

            corona_queue = visit_queues[room_idx][0]
            normal_queue = visit_queues[room_idx][1]

            left_ones = pop_tired_patients(corona_queue, normal_queue, min_visit_end)
            room_queues_length[room_idx] -= left_ones

            if len(corona_queue) > 0 and len(normal_queue) > 0:
                if min_visit_end:
                    # if corona_queue[0][get_col_idx('srv_end')] <= normal_queue[0][get_col_idx('srv_end')]:
                    if corona_queue[0][5] <= normal_queue[0][5]:
                        visiting_patients[room_idx][min_doctor_idx] = corona_queue[0]
                        corona_queue.popleft()
                    # elif corona_queue[0][get_col_idx('srv_end')] <= min_visit_end:
                    elif corona_queue[0][5] <= min_visit_end:
                        visiting_patients[room_idx][min_doctor_idx] = corona_queue[0]
                        corona_queue.popleft()
                    else:
                        visiting_patients[room_idx][min_doctor_idx] = normal_queue[0]
                        normal_queue.popleft()
                else:
                    # if corona_queue[0][get_col_idx('srv_end')] <= normal_queue[0][get_col_idx('srv_end')]:
                    if corona_queue[0][5] <= normal_queue[0][5]:
                        visiting_patients[room_idx][min_doctor_idx] = corona_queue[0]
                        corona_queue.popleft()

                    else:
                        visiting_patients[room_idx][min_doctor_idx] = normal_queue[0]
                        normal_queue.popleft()
            elif len(corona_queue) > 0 and len(normal_queue) == 0:

                visiting_patients[room_idx][min_doctor_idx] = corona_queue[0]
                corona_queue.popleft()

            elif len(corona_queue) == 0 and len(normal_queue) > 0:

                visiting_patients[room_idx][min_doctor_idx] = normal_queue[0]
                normal_queue.popleft()
            else:
                break

            room_queues_length[room_idx] -= 1

            # visiting_srv_end = visiting_patients[room_idx][min_doctor_idx][get_col_idx('srv_end')]
            visiting_srv_end = visiting_patients[room_idx][min_doctor_idx][5]
            if min_visit_end and min_visit_end > visiting_srv_end:
                visit_start = min_visit_end
            else:
                visit_start = visiting_srv_end

            # visiting_patients[room_idx][min_doctor_idx][get_col_idx('visit beg')] = visit_start
            # visiting_patients[room_idx][min_doctor_idx][get_col_idx('room')] = room_idx
            # visiting_patients[room_idx][min_doctor_idx][get_col_idx('doctor')] = min_doctor_idx
            # visit_time = rgs.visit_time(Conf.DOCTORS[room_idx][min_doctor_idx])
            # visiting_patients[room_idx][min_doctor_idx][get_col_idx('visit t')] = visit_time
            # visiting_patients[room_idx][min_doctor_idx][get_col_idx('visit end')] = visit_start + visit_time
            visiting_patients[room_idx][min_doctor_idx][7] = visit_start
            visiting_patients[room_idx][min_doctor_idx][10] = room_idx
            visiting_patients[room_idx][min_doctor_idx][11] = min_doctor_idx
            visit_time = rgs.visit_time(Conf.DOCTORS[room_idx][min_doctor_idx])
            visiting_patients[room_idx][min_doctor_idx][8] = visit_time
            visiting_patients[room_idx][min_doctor_idx][9] = visit_start + visit_time

        if min_room_length > room_queues_length[room_idx]:
            min_room_length = room_queues_length[room_idx]
            min_room_length_idx = room_idx

    return min_room_length_idx


def add_to_room_queue(np_normal_table, np_corona_table, p_index, p_has_corona, visit_queues, room_queues_length,
                      arrive_time, visiting_patients):
    min_room_length_idx = flush_patients(visit_queues,
                                         room_queues_length,
                                         visiting_patients, arrive_time)
    if p_has_corona:
        p = np_corona_table[p_index]
        visit_queues[min_room_length_idx][0].append(p)
        room_queues_length[min_room_length_idx] += 1
    else:
        p = np_normal_table[p_index]
        visit_queues[min_room_length_idx][1].append(p)
        room_queues_length[min_room_length_idx] += 1


def number_of_doctors(doctors):
    num_docs = 0
    for m in doctors: num_docs += len(m)
    return num_docs


if __name__ == '__main__':
    # initialization
    init_pd()
    raw_table = raw_table()
    corona_table = raw_table.loc[raw_table['corona']].reset_index(drop=True)
    normal_table = raw_table.loc[~ raw_table['corona']].reset_index(drop=True)
    visiting_patients = [[None] * len(Conf.DOCTORS[i]) for i in range(len(Conf.DOCTORS))]
    visit_queues = [[deque(), deque()] for i in range(len(Conf.DOCTORS))]
    room_queues_length = [0 for i in range(len(Conf.DOCTORS))]

    # stats arrays
    rooms_length_over_time = [[0 for x in range(len(Conf.DOCTORS))] for y in range(Conf.CLIENT_NO)]
    #response_time = [0 for i in range(len(Conf.CLIENT_NO))]
    # 0: normal,  1: corona plus
    patient_type_over_time = [[0 for x in range(2)] for y in range(Conf.CLIENT_NO)]

    del raw_table
    j_max = Conf.CLIENT_NO // 100

    now = 0
    corona_idx = 0
    normal_idx = 0
    corona_len = len(corona_table)
    normal_len = len(normal_table)


    np_corona_table = corona_table.to_numpy()
    np_normal_table = normal_table.to_numpy()
    corona_as_t_idx = [corona_table.columns.get_loc(c) for c in ['arrival t', 'srv t', 'remaining_P']]
    corona_set_idx = [corona_table.columns.get_loc(c) for c in ['srv beg', 'srv_end', 'remaining_P']]
    normal_set_idx = [normal_table.columns.get_loc(c) for c in ['srv beg', 'srv_end', 'remaining_P']]
    normal_as_t_idx = [normal_table.columns.get_loc(c) for c in ['arrival t', 'srv t', 'remaining_P']]

    del corona_table
    del normal_table



    corona_arrival, corona_srv_t, c_Q_t = np_corona_table[corona_idx, corona_as_t_idx]
    normal_arrival, normal_srv_t, n_Q_t = np_normal_table[normal_idx, normal_as_t_idx]
    queue_arr = np.array([])
    _srv_beg_cache = np.array([])
    for i in range(100):
        print("#" * i + "-" * (99 - i), end="\r")
        for j in range(j_max):
            patient_index = i * j_max + j
            gone = False
            if corona_idx != corona_len and (
                    corona_arrival <= now or corona_arrival <= normal_arrival or normal_idx == normal_len):
                p_index = corona_idx
                p_has_corona = True
                arrival_t = corona_arrival
                begin = now if corona_arrival < now else corona_arrival
                c_Q_t -= (begin - corona_arrival)
                if c_Q_t >= 0:
                    now = end = corona_srv_t + begin
                    np_corona_table[corona_idx, corona_set_idx] = begin, end, c_Q_t
                else:
                    np_corona_table[corona_idx, 6] = "gone"
                    np_corona_table[corona_idx, 5] = "gone"
                    gone = True

                corona_idx += 1
                if corona_idx != corona_len:
                    corona_arrival, corona_srv_t, c_Q_t = np_corona_table[corona_idx, corona_as_t_idx]
            else:
                p_index = normal_idx
                arrival_t = normal_arrival
                p_has_corona = False
                begin = now if normal_arrival < now else normal_arrival
                n_Q_t -= (begin - normal_arrival)
                if n_Q_t >= 0:
                    now = end = normal_srv_t + begin
                    np_normal_table[normal_idx, normal_set_idx] = begin, end, n_Q_t
                else:
                    np_normal_table[normal_idx, 6] = "gone"
                    np_normal_table[normal_idx, 5] = "gone"
                    gone = True
                normal_idx += 1
                if normal_idx != normal_len:
                    normal_arrival, normal_srv_t, n_Q_t = np_normal_table[normal_idx, normal_as_t_idx]

            ix = 0
            _srv_beg_cache = np.append(_srv_beg_cache, begin)
            for e in _srv_beg_cache:
                if e > arrival_t:
                    break
                else:
                    ix += 1
            _srv_beg_cache = _srv_beg_cache[ix:]
            queue_arr = np.append(queue_arr, _srv_beg_cache.shape[0])


            # saving room queue length for stats
            if patient_index != 0:
                for k in range(len(room_queues_length)):
                    rooms_length_over_time[patient_index][k] = room_queues_length[k]

            if gone is False:
                add_to_room_queue(np_normal_table, np_corona_table, p_index, p_has_corona, visit_queues, room_queues_length,
                                  now, visiting_patients)


    print()
    flush_patients(visit_queues, room_queues_length,
                   visiting_patients)

    corona_table = pd.DataFrame(np_corona_table, columns=Conf.TABLE_COLUMNS)
    normal_table = pd.DataFrame(np_normal_table, columns=Conf.TABLE_COLUMNS)
    complete_table = normal_table.append(corona_table, ignore_index=True)



    #mean_corona_plus_insystem_time = (corona_table['visit end'].sum() - corona_table[corona_table['visit end'].isna()]['arrival t'].sum())/len(corona_table['visit end'])
    #mean_corona_minus_insystem_time = (normal_table['visit end'].sum() - normal_table['arrival t'].sum())/len(normal_table['arrival t'])
    #print(len(corona_table[corona_table['visit end'].isna()]['arrival t']))
    #mean_corona_plus_inqueue_time = (corona_table['init_patience'].sum() - corona_table['remaining_P'].sum())/len(corona_table['remaining_P'])
    #mean_corona_minus_inqueue_time = (normal_table['init_patience'].sum() - normal_table['remaining_P'].sum())/len(normal_table['remaining_P'])

    del normal_table, corona_table
    complete_table = complete_table.sort_values(by=['arrival t'], ignore_index=True)

    # getting statistics

    # emtiazi 5
    labels = range(len(complete_table))
    srv_queue_len = queue_arr
    fig, ax = plt.subplots()
    ax.plot(labels, srv_queue_len)
    ax.set(xlabel='time', ylabel='service queue length', title='service queue length plot')
    fig.savefig("plots/Qlen.png")



    statistics_columns = ['in_system_time', 'in_queue_time']
    stats = pd.DataFrame(index=list(range(0, Conf.CLIENT_NO)), columns=statistics_columns)
    stats.loc[:, 'in_system_time'] = 0
    stats.loc[:, 'in_queue_time'] = 0
    #stats.loc[1, 'arrival t'] = 4
    #print(stats)
    gone_counter = 0


    not_gone_table = complete_table[complete_table.remaining_P != 'gone']
    gone_table = complete_table[complete_table.remaining_P == 'gone']
    #print(not_gone_table)

    # in system time
    mean_corona_insystem_time = (gone_table[gone_table.corona == True]['init_patience'].sum() +
                                 not_gone_table[not_gone_table.corona == True]['visit end'].sum() -
                                 not_gone_table[not_gone_table.corona == True]['arrival t'].sum() +
                                 gone_table[gone_table.srv_end != 'gone'][gone_table.corona == True][
                                     'srv t'].sum()) / (len(complete_table[complete_table.corona == True]))

    mean_normal_insystem_time = (gone_table[gone_table.corona != True]['init_patience'].sum()
                                 + not_gone_table[not_gone_table.corona != True]['visit end'].sum() -
                                 not_gone_table[not_gone_table.corona != True]['arrival t'].sum() +
                                 (gone_table[gone_table.srv_end != 'gone'][gone_table.corona != True][
                                      'srv t'].sum())) / (len(complete_table[complete_table.corona != True]))

    mean_corona_inqueue_time = (gone_table[gone_table.corona == True]['init_patience'].sum() +
                                not_gone_table[not_gone_table.corona == True]['visit end'].sum() -
                                not_gone_table[not_gone_table.corona == True]['arrival t'].sum() -
                                not_gone_table[not_gone_table.corona == True]['srv t'].sum() -
                                not_gone_table[not_gone_table.corona == True]['visit t'].sum()) / (
                                   len(complete_table[complete_table.corona == True]))

    mean_normal_inqueue_time = (gone_table[gone_table.corona != True]['init_patience'].sum() +
                                not_gone_table[not_gone_table.corona != True]['visit end'].sum() -
                                not_gone_table[not_gone_table.corona != True]['arrival t'].sum() -
                                not_gone_table[not_gone_table.corona != True]['srv t'].sum() -
                                not_gone_table[not_gone_table.corona != True]['visit t'].sum()) / (
                                   len(complete_table[complete_table.corona != True]))



    overal_insystem_time = (len(complete_table[complete_table.corona == True])*mean_corona_insystem_time + \
                           len(complete_table[complete_table.corona != True])*mean_normal_insystem_time)/\
                           (len(complete_table))

    overal_inqueue_time = (len(complete_table[complete_table.corona == True]) * mean_corona_inqueue_time + \
                            len(complete_table[complete_table.corona != True]) * mean_normal_inqueue_time) / \
                           (len(complete_table))

    print(mean_corona_insystem_time)
    print(mean_normal_insystem_time)
    print(mean_corona_inqueue_time)
    print(mean_normal_inqueue_time)

    # number of gone people
    gone_count = len(gone_table)


    print(rooms_length_over_time)


    #print(queue_arr)
    #print(complete_table)
    #print(complete_table[complete_table.corona != True]['remaining_P'])


    #print(gone_table[gone_table.corona == True]['init_patience'])
    #print((not_gone_table[not_gone_table.corona == True]['visit end'].mean() - not_gone_table[not_gone_table.corona == True]['arrival t'].mean()))


    # for index, patient in complete_table.iterrows():
    #     # in system time calculation
    #     if patient['remaining_P'] is not 'gone':
    #         stats.loc[index, 'in_system_time'] = patient['visit end'] - patient['arrival t']
    #     else:
    #         gone_counter += 1
    #         stats.loc[index, 'in_system_time'] = patient['init_patience']
    #
    #     # in queue time calculation
    #     stats.loc[index, 'in_queue_time'] = patient['init_patience'] - patient['remaining_P']

    # calc mean in-system time
    #mean_insystem_time = (complete_table['visit end'].sum() - complete_table['arrival t'].sum())/len(complete_table['arrival t'])
    #mean_inqueue_time = (complete_table['init_patience'].sum() - complete_table['remaining_P'].sum())/len(complete_table['remaining_P'])



    #print(type(complete_table.loc[2, 'remaining_P']))
    #print(type(complete_table.loc[2, 'init_patience']))
    #print(complete_table)


#!/usr/bin/env python3

from __future__ import division

import queue
import multiprocessing as mp
import logging
from datetime import datetime, timezone
import requests
import os
import time
import sys

from nuvla.api import Api as Nuvla, NuvlaError

RETRY_EXCEPTIONS = (requests.exceptions.ConnectTimeout,)

log = None
log_levels_map = {'info': logging.INFO,
                  'debug': logging.DEBUG,
                  'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'fatal': logging.FATAL,
                  'warn': logging.WARN}


def log_init(config):
    global log

    module_name = os.path.basename(sys.argv[0]).replace('.py', '')

    log_level = log_levels_map.get(config.get('logging', {}).get('level', 'info').lower())
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(process)d - %(levelname)s - %(message)s')

    log = logging.getLogger(module_name)
    log.setLevel(log_level)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(log_formatter)
    log.addHandler(stdout_handler)

    if config.get('logging', {}).get('file', False):
        if config['logging'].get('fn'):
            log_file = '{0}.log.{1}'.format(config['logging']['fn'], int(time.time()))
        else:
            log_file = '{0}.log.{1}'.format(module_name, int(time.time()))
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_formatter)
        log.addHandler(file_handler)


def nuvla_init(config):
    log.info("Authenticating with Nuvla...")
    nuvla = Nuvla(endpoint=config.get('nuvla', {}).get('endpoint'), insecure=True)
    n = 0
    ts = time.time()
    while True:
        try:
            nuvla.login_password(config['nuvla']['username'], config['nuvla']['password'])
            break
        except RETRY_EXCEPTIONS as ex:
            log.error("Authenticating with Nuvla... failed: {}".format(ex))
            st = 2 ** n
            log.info("Authenticating with Nuvla... re-attempting in {} sec.".format(st))
            time.sleep(st)
            n = (n < 7) and (n + 1) or 0
    log.info("Authenticating with Nuvla... done. (time took: {} sec)".format(int(time.time() - ts)))
    return nuvla


def compose_filter():
    filter_base = "platform='S3' and name='GNSS'"
    filter_criteria = config['stations']['criteria']

    filter_gnss = filter_base
    if len(filter_criteria) > 0:
        filter_gnss += " and " + filter_criteria
    return filter_gnss


def metrics(mp_queue: mp.Queue):
    ms = {}
    vals = {}
    ts_rate = time.time()
    ts_stat = time.time()
    while True:
        log.debug('waiting from queue...')
        try:
            v = mp_queue.get(block=True, timeout=0.1)
            name = v[0]
            tm = round(v[1], 3)
            log.debug('waiting from queue... done. {0} {1}'.format(name, tm))
            if name not in ms:
                ms[name] = {'count': 0,
                            '_count_priv': 0,
                            'm1_rate': 0,
                            'mean': 0}
                vals[name] = []
            ms[name]['count'] = ms[name]['count'] + 1
            vals[name].append(tm)
            ms[name]['mean'] = round(sum(vals[name]) / ms[name]['count'], 3)
        except queue.Empty:
            # log.error('Queue EMPTY...')
            pass
        if time.time() - ts_rate >= 60:
            # have a separate thread to run this.
            rate_total = 0
            for n in ms.keys():
                ms[n]['m1_rate'] = round((ms[n]['count'] - ms[n]['_count_priv']) / 60.0, 3)
                rate_total += ms[n]['m1_rate']
                log.info('RATE: {0} m1_rate: {1}'.format(n, ms[n]['m1_rate']))
                ms[n]['_count_priv'] = ms[n]['count']
            log.info('RATE TOTAL: {}'.format(round(rate_total, 3)))
            ts_rate = time.time()
        if time.time() - ts_stat >= 10:
            log.info('STATS: {}'.format(ms))
            ts_stat = time.time()


def dr_create(input):
    log.info('will create....')
    conf = input['config']
    q_metrics = input['queue']
    nuvla = nuvla_init(conf)
    num_create = conf.get('num-create', -1)
    num_total = 0
    while True:
        ts = time.time()
        try:
            tm = datetime.utcnow().replace(tzinfo=timezone.utc) \
                .replace(microsecond=0).isoformat().replace('+00:00', 'Z')
            object.update({'timestamp': tm})
            res = nuvla.add('data-record', object)
            if res.data['status'] != 201:
                log.error('Failed to create object.')
            else:
                log.debug('Created object.')
        except Exception as ex:
            log.warning('Exception while adding data-record: {}'.format(ex))
        q_metrics.put_nowait((os.getpid(), time.time() - ts))
        time.sleep(0.1)
        num_total += 1
        if 0 < num_create <= num_total:
            break


def dr_delete(input):
    def _nuvla_deregister(nuvla, dr_id, stat):
        try:
            log.info(stat.format('Nuvla de-register:'))
            nuvla._cimi_request('DELETE', dr_id)
            # nuvla.delete(so['id'])
            return True
        except NuvlaError as ex:
            log.info("WARNING: {0}. {1}".format(stat.format('Nuvla failed to de-register:'), ex.reason))
            return False

    nuvla = nuvla_init(input['config'])
    log.info("# of data records to delete: {}".format(len(input["data_records"])))
    work_size = len(input["data_records"])
    n = work_size
    for dr in input["data_records"]:
        dr_id = dr['id']
        obj = dr['object']
        stat = '#{0}/{1} {{}} {2} {3}'.format(n, work_size, obj, dr_id)
        if not _nuvla_deregister(nuvla, dr_id, stat):
            log.error(stat.format('Failed to delete'))
        n -= 1


def data_records_to_delete(nuvla: Nuvla, obj_num, filter, size_bytes_after, page_size, thresholdLow_station):
    data_records = []
    # Pagination.
    first = 1
    if obj_num < page_size:
        last = obj_num
    else:
        last = page_size
    log.info('filter: {}'.format(filter))
    orderby = 'gnss:timestamp:asc'
    log.info('orderby: {}'.format(orderby))
    aggrs = 'sum:bytes'
    log.info('aggregations: {}'.format(aggrs))
    select = 'id,bucket,object,bytes'
    log.info('select: {}'.format(select))
    while (size_bytes_after > thresholdLow_station) and (last <= obj_num):
        log.info("Collecting data-records with paging: {0} {1} {2} {3}"
                 .format(size_bytes_after, thresholdLow_station, first, last))
        res = nuvla.search('data-record',
                           filter=filter,
                           orderby=orderby,
                           aggregation=aggrs,
                           first=first,
                           last=last,
                           select=select)
        drs = []
        for dr in res.data['resources']:
            drs.append(dr)
            size_bytes_after -= dr['bytes']
            if size_bytes_after < thresholdLow_station:
                log.info("size_bytes_after {0} below or equal watermark {1}. Ready to delete."
                         .format(size_bytes_after, thresholdLow_station))
                break
        data_records.append(drs)
        first = last + 1
        last += page_size
    return data_records


object = {
    "description": "GNSS",
    "gnss:size": 49999800,
    "name": "GNSS",
    "gnss:lon": -1.1837999820709229,
    "infrastructure-service": "infrastructure-service/67df92a2-9553-46f3-88ee-0b1adfb53d7e",
    "gnss:bits": 8,
    "gnss:lat": 52.95220184326172,
    "gnss:unit_id": "00001",
    "gnss:hgt": 99,
    "gnss:timestamp": "20191003T144657Z",
    "host": "10.1.78.32:8080",
    "gnss:name": "perf-test-20191003T144657Z",
    "resource-type": "data-record",
    "content-type": "gnss/perf-test",
    "gnss:chain": 1,
    "bytes": 49999800,
    "timestamp": "2019-10-03T14:46:57Z",
    "gnss:type": "perf-test",
    "location": [
        52.95220184326172,
        -1.1837999820709229,
        99
    ],
    "object": "perf-test-20191003T144657Z",
    "bucket": "bucket-perf-test-20191003t140000z",
    "gnss:station": "nuvlabox-esac",
    "platform": "S3"
}


def create_data_key_prefix(nuvla):
    try:
        nuvla.add('data-record-key-prefix',
                  {"prefix": "gnss",
                   "uri": "http://sixsq.com/nuvla/schema/1/data/gnss"})
    except Exception as ex:
        if ex.response.status_code != 409:
            raise ex


def creator(config, nc):
    q = mp.Queue()

    p_metrics = mp.Process(target=metrics, args=(q,))
    p_metrics.start()

    input = {'config': config,
             'queue': q}
    creators = []
    for _ in range(nc):
        p = mp.Process(target=dr_create, args=(input,))
        p.start()
        creators.append(p)

    # map(lambda c: c.join(), creators)

    # p_metrics.join()


def creator_simple(config, nc):
    q = mp.Queue()
    input = {'config': config,
             'queue': q}
    create_data_key_prefix(nuvla_init(config))
    dr_create(input)


def pruner(config):
    stations = config['stations']
    num_stations = len(stations['names'])
    conf_st_threshold = int(stations['threshold_bytes'] / num_stations)
    thresholdMiddle_station = int(conf_st_threshold * 0.95)
    thresholdLow_station = int(conf_st_threshold * 0.93)

    page_size = config["page-size"]
    sleep_minutes = config["sleep-minutes"]

    pool_size = config['pool-size']

    ES_STUPID_LIMIT = 10000

    station = 'nuvlabox-esac'

    while True:
        log.info("========== {} ==========".format(datetime.now()))
        t0 = time.time()

        nuvla = nuvla_init(config)

        log.info('~' * 25)
        log.info("Station: {}".format(station))

        # find
        filter = compose_filter() + " and gnss:station='{}'".format(station)
        log.info("filter: {}".format(filter))
        aggr_sum_bytes = 'sum:bytes'
        aggr_count = 'value_count:id'
        aggregation = '{0},{1}'.format(aggr_sum_bytes, aggr_count)
        res = nuvla.search('data-record', filter=filter, aggregation=aggregation, last=0, select='')
        size_bytes = int(res.data['aggregations'][aggr_sum_bytes]['value'])
        log.info('size bytes: {}'.format(size_bytes))
        obj_num = int(res.data['aggregations'][aggr_count]['value'])
        if obj_num > ES_STUPID_LIMIT:
            # Otherwise, paging fails.
            log.info('WARNING: reduced records number from {0} to default {1}'.format(obj_num, ES_STUPID_LIMIT))
            obj_num = ES_STUPID_LIMIT
        log.info("Station: {0} Count: {1} Total size: {2} ThrhldHigh: {3} ThrhldMiddle: {4} ThrhldLow: {5}"
                 .format(station, obj_num, size_bytes, conf_st_threshold, thresholdMiddle_station,
                         thresholdLow_station))
        if size_bytes <= thresholdMiddle_station:
            log.info("Station skipped: {0} Total size {1} < ThrhldMiddle {2}"
                     .format(station, size_bytes, thresholdMiddle_station))
            continue

        data_records = data_records_to_delete(nuvla, obj_num, filter, size_bytes, page_size, thresholdLow_station)
        inputs = []
        # Only one input parameter is allowed by mapper and S3 is not
        # pickle-able and can't be passed as part of input to any
        # multiprocessing process/thread. Provide the whole config instead.
        for drs in data_records:
            inputs.append({"config": config, "data_records": drs})
        log.info('Ready to delete and deregister....')
        with mp.Pool(pool_size) as p:
            p.map(dr_delete, inputs)

        log.info('Cleanup iteration took {0:.2f} sec.'.format(time.time() - t0))
        time.sleep(sleep_minutes * 60)


if __name__ == "__main__":
    conf_file = 'dr_wd.conf'
    config = {
        "nuvla": {
            "username": "super",
            "endpoint": "https://localhost",
            "password": "supeR8-supeR8",
            # "endpoint": "https://89.145.167.236",
            # "password": "Rorca*THvq@j4vtz"
        },
        "stations": {
            "names": ['nuvlabox-esac'],
            "threshold_bytes": 100,
            "criteria": "gnss:type='perf-test'"
        },
        "num-create": 1,
        "page-size": 500,
        "sleep-minutes": 0.1,
        "pool-size": 1,
        "force-dereg": False,
        "logging": {
            "level": "info",
            "file": True,
            "fn": None
        }
    }

    # if len(sys.argv) > 1:
    #     conf_file = sys.argv[1]
    # print('Using config: {}'.format(conf_file))
    # with open(conf_file) as fh:
    #     config.update(json.loads(fh.read()))

    who = None
    if len(sys.argv) > 1:
        who = sys.argv[1]
        config['logging']['fn'] = sys.argv[1]

    log_init(config)
    if 'creator-simple' == who:
        print('simple creator')
        creator_simple(config, 25)
    elif 'creator' == who:
        creator(config, 1)
    elif 'deleter' == who:
        pruner(config)
    else:
        print('creator or deleter?')

import ncm
from csclient import EventingCSClient
import time
import json

api_keys = {
    'X-CP-API-ID': 'your',
    'X-CP-API-KEY': 'api',
    'X-ECM-API-ID': 'keys',
    'X-ECM-API-KEY': 'here'
}

n = ncm.NcmClient(api_keys=api_keys, log_events=False)
cp = EventingCSClient('custom2_info')

def check_uptime(uptime_req):
    uptime  = int(cp.get('status/system/uptime'))
    cp.log(f'Current uptime: {uptime} seconds')
    if uptime < uptime_req:
        cp.log(f'Sleeping for {uptime_req - uptime} seconds')  
        time.sleep(uptime_req - uptime)
    cp.log('Uptime check passed, continuing...')
    return


def get_router_id():
    cp.log('Getting router_id for device...')
    router_id = cp.get('status/ecm/client_id')
    cp.log(f'router_id is {router_id}, continuing...')

    return router_id


def enable_client_usage():
    client_usage_enabled = cp.get('status/client_usage/enabled')
    while not client_usage_enabled:
        cp.log('Enabling client data usage...')
        cp.put('config/stats/client_usage/enabled', True)
        time.sleep(5)
        client_usage_enabled = cp.get('status/client_usage/enabled')
    cp.log('Client data usage enabled, continuing...')

    return client_usage_enabled


def get_client_data():
    cp.log('Getting client data...')
    client_data = cp.get('status/client_usage/stats')
    client_dict = {}
    for client in client_data:
        client_dict[client['name']] = client['ip']
    client_dict = {'total clients': len(client_dict), 'clients': client_dict}
    cp.log(f'client data: {client_dict}')

    return client_dict


def put_custom2(router_id, client_dict, uptime_req):
    custom2_value = json.dumps(client_dict)
    ncm_state = cp.get('status/ecm/state')
    ncm_uptime = int(cp.get('status/ecm/uptime'))
    cp.log(f'NCM state is {ncm_state} and NCM uptime is {ncm_uptime} seconds')
    if ncm_state != 'connected' or ncm_uptime < uptime_req:
        cp.log(f'NCM not connected or uptime less than {uptime_req}, not setting custom 2 field...')
        return
    else:
        cp.log(f'NCM connected and uptime requirement met, setting custom 2 field...')
        n.v2.set_custom2(router_id=router_id, text=custom2_value)
        cp.log('NCM custom 2 field set, continuing...')
        return


if __name__ == '__main__':
    cp.log('Starting custom2_info script...')
    sleep_timer = 300
    uptime_req = 120
    check_uptime(uptime_req=uptime_req)
    router_id = get_router_id()
    client_usage_enabled = enable_client_usage()
    while client_usage_enabled:
        client_dict = get_client_data()
        put_custom2(router_id=router_id, client_dict=client_dict, uptime_req=uptime_req)
        cp.log(f'Sleeping for {sleep_timer} seconds...')
        time.sleep(300)

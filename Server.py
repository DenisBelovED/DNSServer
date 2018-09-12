import pickle
import socket
from datetime import timedelta, datetime
from dnslib import DNSError, DNSRecord


class Packet:
    def __init__(self, rr, create_time):
        self.resource_record = rr
        self.create_time = create_time


def load_history():
    try:
        with open('data.pickle', 'rb') as f:
            database = pickle.load(f)
        print('history loaded')
    except:
        print('history not exist')
        return None
    return database


def save_history(data):
    try:
        with open('data.pickle', 'wb') as f:
            pickle.dump(data, f)
        print('dumping successful')
    except:
        print('dumping error')


def is_expired(packet):
    return datetime.now() - packet.create_time > timedelta(seconds=packet.resource_record.ttl)


def clear_outdated_cash(database):
    cache_delta = 0
    for key, value in database.items():
        old_length = len(value)
        database[key] = set(packet for packet in value if not is_expired(packet))
        cache_delta += old_length - len(database[key])
    if cache_delta > 0:
        print(str(datetime.now()) + " - cleared " + str(cache_delta) + " resource records")


'''def add_record(rr):
    k = (str(rr.rname).lower(), rr.rtype)
    if k in database:
        database[k].add(Pair(rr, dt.now()))
    else:
        database[k] = {Pair(rr, dt.now())}

'''
def add_records(dns_record, database):
    for r in dns_record.rr + dns_record.auth + dns_record.ar:
        if r.rtype in {1, 2}:
            add_record(r)
            log("Record added.")


def work_loop(database, sock):
    try:
        while True:
            data, addr = sock.recvfrom(2048)
            #clear_outdated_cash(database)
            try:
                dns_record = DNSRecord.parse(data)
            except DNSError:
                print('getting incorrect query, packet ignored')
                continue

            add_records(dns_record, database)
            '''if not r.header.qr:
                resp = get_resp(r)
                try:
                    send_to(get_with_caching() if resp is None else resp.pack(), *addr)
                    log("Response sent.")
                except (OSError, DNSError):
                    log("Failed to respond.")'''
    except:
        print('server error')


def main():
    print('server started')
    database = load_history()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 40000))

    work_loop(database, sock)

    if database:
        save_history(database)
    print('server stop')


if __name__ == '__main__':
    main()

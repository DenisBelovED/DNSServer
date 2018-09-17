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


def add_record(rr, database, date_time):
    k = (str(rr.rname).lower(), rr.rtype)
    if k in database:
        database[k].add(Packet(rr, date_time))
    else:
        database[k] = {Packet(rr, date_time)}


def add_records(dns_record, database):
    for r in dns_record.rr + dns_record.auth + dns_record.ar:
        if r.rtype in {1, 2}:
            date_time = str(datetime.now())
            add_record(r, database, date_time)
            print(date_time + " - DNS record added.")


def get_response(dns_record, database):
    if dns_record.q.qtype in {1, 2}:
        key = (str(dns_record.q.qname).lower(), dns_record.q.qtype)
        try:
            if key in database and database[key]:
                reply = dns_record.reply()
                reply.rr = [p.rr for p in database[key]]
                return reply
        except:
            pass


def send_response(response, addr):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(addr)
    sock.sendall(response)
    sock.close()


def work_loop(database, sock):
    try:
        while True:
            data, addr = sock.recvfrom(2048)

            if database:
                clear_outdated_cash(database)

            try:
                dns_record = DNSRecord.parse(data)
            except DNSError:
                print('getting incorrect query, packet ignored')
                continue

            add_records(dns_record, database)
            if not dns_record.header.qr:
                response = get_response(dns_record, database)
                try:
                    if response:
                        send_response(sock, response.pack())
                    else:
                        resp = dns_record.send("ns1.e1.ru")
                        add_records(DNSRecord.parse(resp), database)
                        send_response(resp, addr)
                    print(str(datetime.now()) + " - response send")
                except (OSError, DNSError):
                    print(str(datetime.now()) + " - transmission error")
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

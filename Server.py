import pickle


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


def main():
    print('server started')
    database = load_history()

    if database:
        save_history(database)
    print('server stop')


if __name__ == '__main__':
    main()

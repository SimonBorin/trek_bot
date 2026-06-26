import trek
from types import SimpleNamespace


class FakeCollection:
    def __init__(self):
        self.store = {}

    def delete_one(self, query):
        self.store.pop(query['_id'], None)

    def update_one(self, query, update, upsert=False):
        doc = self.store.setdefault(query['_id'], {'_id': query['_id']})
        doc.update(update['$set'])

    def find_one(self, query):
        return self.store[query['_id']]


class FakeMessage:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.message_id = 1
        self.replies = []

    def reply_text(self, text, **kwargs):
        self.replies.append((text, kwargs))


class FakeBot:
    def __init__(self):
        self.edits = []

    def edit_message_text(self, **kwargs):
        self.edits.append(kwargs)


def fake_update(chat_id, user_id, data='restart'):
    chat = SimpleNamespace(id=chat_id)
    user = SimpleNamespace(id=user_id, username=f'user{user_id}', first_name='Test', last_name='Player')
    message = FakeMessage(chat_id)
    callback_query = SimpleNamespace(data=data, message=message)
    return SimpleNamespace(
        effective_chat=chat,
        effective_user=user,
        effective_message=message,
        callback_query=callback_query,
    )


def test_import_does_not_configure_external_services():
    assert trek.client is None
    assert trek.parameters_db is None
    assert trek.sub_param_db is None


def test_short_range_scan_marks_docked_next_to_starbase():
    sector = [0] * 64
    sector[0] = 4
    sector[1] = 2

    condition, scan = trek.srs(sector, 0)

    assert condition == 'Docked'
    assert '-O-' in scan
    assert '<O>' in scan


def test_addshields_moves_energy_to_shields():
    energy, shields = trek.addshields(3000, 0, 500)

    assert energy == 2500
    assert shields == 500


def test_direct_chat_players_have_separate_game_state(monkeypatch):
    parameters = FakeCollection()
    sub_params = FakeCollection()
    monkeypatch.setattr(trek, 'parameters_db', parameters)
    monkeypatch.setattr(trek, 'sub_param_db', sub_params)
    context = SimpleNamespace(bot=FakeBot())

    trek.start_game(fake_update(chat_id=100, user_id=100), context)
    trek.start_game(fake_update(chat_id=200, user_id=200), context)

    assert set(parameters.store) == {100, 200}
    assert parameters.store[100]['chat_id'] == 100
    assert parameters.store[200]['chat_id'] == 200

    sub_params.store[100]['shields_flag'] = 1
    trek.num_menu(fake_update(chat_id=100, user_id=100, data='5'), context)

    assert parameters.store[100]['num_input'] == '5'
    assert parameters.store[200]['num_input'] == ''

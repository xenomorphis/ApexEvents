from datetime import date
from pyplanet.views.generics.list import ManualListView
from pyplanet.utils import times


class EventListView(ManualListView):

    app = None

    title = 'LEVEL9 – Current leaderboard'
    icon_style = 'Icons128x128_1'
    icon_substyle = 'Browse'
    viewer = None

    data = []

    def __init__(self, app, viewer):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.viewer = viewer

        if self.app.tournament_day != date.today():
            self.title = 'LEVEL9 – Leaderboard from ' + self.app.tournament_day

    async def get_fields(self):
        return [
            {
                'name': 'Rank',
                'index': 'pos',
                'sorting': True,
                'searching': False,
                'width': 15,
                'type': 'label'
            },
            {
                'name': 'Player',
                'index': 'player_name',
                'sorting': False,
                'searching': True,
                'width': 100,
                'type': 'label'
            },
            {
                'name': 'Total Time',
                'index': 'total_time',
                'sorting': True,
                'searching': False,
                'width': 45
            },
            {
                'name': 'Maps finished',
                'index': 'maps_finished',
                'sorting': True,
                'searching': False,
                'width': 30
            },
        ]

    async def get_data(self):
        items = []

        for pos in range(1, len(self.app.tournament_pos) + 1):
            player = self.app.tournament_pos[pos]
            player_finished = self.app.finished_maps[player]
            player_time = self.app.tournament_times[player]

            if pos == 1:
                if len(times.format_time(player_time)) < 9:
                    if player == self.viewer:
                        items.append(
                            {'pos': '$FB1' + str(pos), 'player_name': player,
                             'total_time': '$FB10' + times.format_time(player_time),
                             'maps_finished': '$FB1' + str(player_finished) + '/' + str(self.app.current_map - 1)})
                    else:
                        items.append(
                            {'pos': pos, 'player_name': player, 'total_time': '0' + times.format_time(player_time),
                             'maps_finished': str(player_finished) + '/' + str(self.app.current_map - 1)})

                else:
                    if player == self.viewer:
                        items.append(
                            {'pos': '$FB1' + pos, 'player_name': player,
                             'total_time': '$FB1' + times.format_time(player_time),
                             'maps_finished': '$FB1' + str(player_finished) + '/' + str(self.app.current_map - 1)})
                    else:
                        items.append({'pos': pos, 'player_name': player, 'total_time': times.format_time(player_time),
                                      'maps_finished': str(player_finished) + '/' + str(self.app.current_map - 1)})

            else:
                rel_time = self.app.tournament_times[player] - self.app.tournament_times[self.app.tournament_pos[1]]

                if player == self.viewer:
                    items.append({'pos': '$FB1' + str(pos), 'player_name': player,
                                  'total_time': '$FB1+' + times.format_time(rel_time),
                                  'maps_finished': '$FB1' + str(player_finished) + '/' + str(self.app.current_map - 1)})
                else:
                    items.append({'pos': pos, 'player_name': player, 'total_time': '+' + times.format_time(rel_time),
                                  'maps_finished': str(player_finished) + '/' + str(self.app.current_map - 1)})

        return items

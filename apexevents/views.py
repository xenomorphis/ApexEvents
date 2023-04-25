from datetime import date
from pyplanet.views import TemplateView
from pyplanet.views.generics.list import ManualListView
from pyplanet.utils import times


class Lvl9ListView(ManualListView):
    app = None
    title = 'LEVEL9 – Current leaderboard'
    icon_style = 'Icons128x128_1'
    icon_substyle = 'Statistics'
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
                        items.append({'pos': '$FB1' + str(pos),
                                      'player_name': player,
                                      'total_time': '$FB10' + times.format_time(player_time),
                                      'maps_finished': '$FB1' + str(player_finished) + '/' + str(self.app.current_map - 1)})
                    else:
                        items.append({'pos': pos,
                                      'player_name': player,
                                      'total_time': '0' + times.format_time(player_time),
                                      'maps_finished': str(player_finished) + '/' + str(self.app.current_map - 1)})

                else:
                    if player == self.viewer:
                        items.append({'pos': '$FB1' + str(pos),
                                      'player_name': player,
                                      'total_time': '$FB1' + times.format_time(player_time),
                                      'maps_finished': '$FB1' + str(player_finished) + '/' + str(self.app.current_map - 1)})
                    else:
                        items.append({'pos': pos,
                                      'player_name': player,
                                      'total_time': times.format_time(player_time),
                                      'maps_finished': str(player_finished) + '/' + str(self.app.current_map - 1)})

            else:
                rel_time = self.app.tournament_times[player] - self.app.tournament_times[self.app.tournament_pos[1]]

                if player == self.viewer:
                    items.append({'pos': '$FB1' + str(pos),
                                  'player_name': player,
                                  'total_time': '$FB1+' + times.format_time(rel_time),
                                  'maps_finished': '$FB1' + str(player_finished) + '/' + str(self.app.current_map - 1)})
                else:
                    items.append({'pos': pos,
                                  'player_name': player,
                                  'total_time': '+' + times.format_time(rel_time),
                                  'maps_finished': str(player_finished) + '/' + str(self.app.current_map - 1)})

        return items


class SummitListView(ManualListView):
    app = None
    title = 'SUMMIT – Preliminary Round'
    icon_style = 'Icons128x128_1'
    icon_substyle = 'Statistics'
    viewer = None

    data = []

    def __init__(self, app, viewer):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.player_manager = app.instance.player_manager
        self.viewer = viewer

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
                'name': 'Total Points',
                'index': 'points',
                'sorting': True,
                'searching': False,
                'width': 30
            },
        ]

    async def get_data(self):
        items = []

        for pos in range(1, len(self.app.tournament_pos) + 1):
            player_login = self.app.tournament_pos[pos]
            player_points = self.app.tournament_players[player_login]

            if pos < 13:
                if player_login == self.viewer:
                    items.append({'pos': '$1EF' + str(pos),
                                  'player_name': self.app.tournament_player_names[player_login],
                                  'points': '$1EF' + str(player_points)})
                else:
                    items.append({'pos': pos,
                                  'player_name': self.app.tournament_player_names[player_login],
                                  'points': str(player_points)})

            else:
                if player_login == self.viewer:
                    items.append({'pos': '$1EF' + str(pos),
                                  'player_name': self.app.tournament_player_names[player_login],
                                  'points': '$1EF' + str(player_points)})
                else:
                    items.append({'pos': '$D00' + str(pos),
                                  'player_name': self.app.tournament_player_names[player_login],
                                  'points': '$D00' + str(player_points)})

        return items


class EventToolbar(TemplateView):
    template_name = 'apexevents/event_toolbar.xml'

    def __init__(self, app, *args, **kwargs):
        """
        :param app: App instance.
        :type app: pyplanet.apps.contrib.info.Info
        """
        super().__init__(*args, **kwargs)
        self.app = app
        self.commands = {
            'results_level9': '/lvl9rank 1',
            'results_summit': '/summitrank',
        }
        self.id = 'apexevents'
        self.manager = self.app.context.ui

    async def get_context_data(self):
        context = await super().get_context_data()
        return context

    async def handle_catch_all(self, player, action, values, **kwargs):
        action += '_' + self.app.tournament

        if action not in self.commands:
            return

        await self.app.instance.command_manager.execute(player, self.commands[action])

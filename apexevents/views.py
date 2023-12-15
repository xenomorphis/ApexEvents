from datetime import date
from pyplanet.views import TemplateView
from pyplanet.views.generics.list import ManualListView
from pyplanet.utils import times


class EventToolbarView(TemplateView):
    template_name = 'apexevents/event_toolbar.xml'

    def __init__(self, app):
        super().__init__(app.context.ui)

        self.app = app
        self.id = 'apexevents_toolbar'

        self.subscribe('results', self.action_results)

    async def get_context_data(self):
        data = await super().get_context_data()
        return data

    async def action_results(self, player, *args, **kwargs):
        if 'summit' in self.app.tournament:
            return await self.app.instance.command_manager.execute(player, '/summitrank')
        elif 'level9' in self.app.tournament:
            return await self.app.instance.command_manager.execute(player, '/lvl9rank')


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
            raw_time = self.app.tournament_times[player]
            color_code = ''

            if pos == 1 and len(times.format_time(raw_time)) < 9:
                player_time = '0' + times.format_time(raw_time)
            elif pos == 1 and len(times.format_time(raw_time)) > 8:
                player_time = times.format_time(raw_time)
            else:
                rel_time = raw_time - self.app.tournament_times[self.app.tournament_pos[1]]
                player_time = '+' + times.format_time(rel_time)

            if player == self.viewer:
                color_code = '$FB1'

            items.append({'pos': color_code + str(pos),
                          'player_name': player,
                          'total_time': color_code + player_time,
                          'maps_finished': color_code + str(player_finished) + '/' + str(self.app.current_map - 1)})

        return items


class SummitPreliminaryListView(ManualListView):
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
        players_current = len(self.app.tournament_pos)

        if players_current > 17:
            q_limit = 15
        else:
            q_limit = 13

        for pos in range(1, len(self.app.tournament_pos) + 1):
            player_login = self.app.tournament_pos[pos]
            player_points = self.app.tournament_players[player_login]
            color_code = ''

            if pos >= q_limit:
                color_code = '$D00'

            if player_login == self.viewer:
                color_code = '$1EF'

            items.append({'pos': color_code + str(pos),
                          'player_name': self.app.tournament_player_names[player_login],
                          'points': color_code + str(player_points)})

        return items

import math

from pyplanet.views.generics.list import ManualListView

from pyplanet.utils import times


class EventListView(ManualListView):
    # based on https://github.com/PyPlanet/PyPlanet/blob/master/pyplanet/apps/contrib/jukebox/views.py
    app = None

    title = 'Current event leaderboard'
    icon_style = 'Icons128x128_1'
    icon_substyle = 'Browse'

    data = []

    def __init__(self, app):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui

    async def get_fields(self):
        return [
            {
                'name': 'Position',
                'index': 'pos',
                'sorting': True,
                'searching': False,
                'width': 20,
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
                'width': 40
            },
        ]

    async def get_data(self):
        items = []

        for pos in range(1, len(self.app.tournament_pos) + 1):
            player = self.app.tournament_pos[pos]
            player_time = self.app.tournament_times[player]

            if pos == 1:
                items.append({'pos': pos, 'player_name': player, 'total_time': times.format_time(player_time)})
            else:
                rel_time = self.app.tournament_times[player] - self.app.tournament_times[self.app.tournament_pos[1]]
                items.append({'pos': pos, 'player_name': player, 'total_time': times.format_time(rel_time)})

        return items

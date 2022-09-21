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
                'index': 'index',
                'sorting': True,
                'searching': False,
                'width': 10,
                'type': 'label'
            },
            {
                'name': 'Player',
                'index': 'map_name',
                'sorting': True,
                'searching': True,
                'width': 100,
                'type': 'label'
            },
            {
                'name': 'Total Time',
                'index': 'player_nickname',
                'sorting': True,
                'searching': False,
                'width': 50
            },
        ]

    async def get_data(self):
        index = 1
        items = []
        for item in self.app.jukebox:
            items.append({'index': index, 'map_name': item['map'].name, 'player_nickname': item['player'].nickname,
                          'player_login': item['player'].login})
            index += 1

        return items

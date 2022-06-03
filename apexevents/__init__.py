import asyncio
import time

from pyplanet.apps.config import AppConfig
from pyplanet.contrib.command import Command
from pyplanet.utils import times

from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals

class ApexEvents(AppConfig):
    name = 'pyplanet.apps.contrib.apexevents'
    game_dependencies = ['trackmania']
    app_dependencies = ['core.maniaplanet']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.lock = asyncio.Lock()
        
        self.tournament = ''
        self.current_map = 0
        self.map_times = dict()
        self.tournament_pos = dict()
        self.tournament_times = dict()
        self.tournament_dnf = 0
    
    async def on_start(self):
        await self.instance.permission_manager.register('manage_event', 'Enables access to the AutoModerator configuration commands.', app=self, min_level=1)
        await self.instance.permission_manager.register('dev', 'Enables access to developer commands.', app=self, min_level=3)
    
        await self.instance.command_manager.register(
            Command(command='lvl9start', target=self.level9_start, perms='apexevents:manage_event', admin=True,
                    description='Starts the AutoMod-Tool'),
            Command(command='lvl9clear', target=self.level9_clear, perms='apexevents:manage_event', admin=True,
                    description='Resets the AutoMod-Tool'),
            Command(command='lvl9rank', aliases=['lvl9'], target=self.level9_rank, description='Shows current ranking information.'),
            Command(command='rulebook', target=self.rules, description='Shows link to the rules for the current tournament.'),
            Command(command='apexevents', target=self.apexevents_info),
            Command(command='aedebug', target=self.debug, perms='apexevents:dev', admin=True)
        )
        
        self.context.signals.listen(mp_signals.map.map_begin, self.map_begin)
        self.context.signals.listen(mp_signals.map.map_end, self.map_end)
        self.context.signals.listen(tm_signals.finish, self.player_finish)   #oder mal tm_signals.scores probieren

    async def level9_start(self, player, data, **kwargs):
        if self.tournament == '':
            await self.instance.chat('$s$FB3Auto$FFFModerator: Good Evening and welcome to another $FB3LEVEL9 $FFFtournament! GLHF!')
            self.tournament = 'level9'
            self.current_map = 0
            self.map_times.clear()
            self.tournament_times.clear()
            self.tournament_dnf = 0
    
    async def level9_clear(self, player, data, **kwargs):
        if self.tournament == 'level9':
            self.tournament = ''
        
            self.current_map = 0
            self.map_times.clear()
            self.tournament_times.clear()
            self.tournament_dnf = 0
        
            await self.instance.chat('$s$FB3Auto$FFFModerator: Tournament successfully cleared!', player)

    async def level9_rank(self, player, data, **kwargs):
        # Gibt auf Anfrage die aktuelle Position des Spielers in der Turnierrangliste zurück.
        if player.nickname in self.tournament_pos.values():
            player_pos = list(self.tournament_pos.keys())[list(self.tournament_pos.values()).index(player.nickname)]
            player_total = self.tournament_times[player.nickname]
        
            if player_pos > 1:
                player_prev = self.tournament_pos[player_pos - 1]
                player_prev_total = self.tournament_times[player_prev]
                time_diff = abs(player_prev_total - player_total)
                await self.instance.chat('$s$FFF Next rank ahead: $FE0{}. {}  $FE0-{}'
                                         .format((player_pos - 1), player_prev, times.format_time(time_diff)), player)

            await self.instance.chat('$s$FFF Your current rank: $1EF{}. {}  $1EF{}'.format(player_pos, player.nickname,
                                             times.format_time(self.tournament_times[player.nickname])), player)
            
            if player_pos < len(self.tournament_pos):
                player_next = self.tournament_pos[player_pos + 1]
                player_next_total = self.tournament_times[player_next]
                time_diff = abs(player_next_total - player_total)
                await self.instance.chat('$s$FFF Next rank behind: $FE0{}. {}  $FE0+{}'
                                         .format((player_pos + 1), player_next, times.format_time(time_diff)), player)
        else:
            await self.instance.chat('$s$FFF You don\'t have a tournament ranking yet. Finish a map to get one.', player)
    
    async def show_results(self):
        if self.tournament == 'level9':
            time.sleep(7.5)
            await self.instance.chat('$s$FB3Auto$FFFModerator: The tournament is concluded. Here are the final results:')

            for pos in range(1, len(self.tournament_pos)):
                player = self.tournament_pos[pos]
                player_time = self.tournament_times[player]

                if pos == 1:
                    suffix = 'st'
                    await self.instance.chat('$s$FFF// $1EF{}{}: {}  $1EF{}'.format(str(pos), suffix, player, times.format_time(player_time)))
                elif pos == 2:
                    suffix = 'nd'
                    rel_time = self.tournament_times[player] - self.tournament_times[self.tournament_pos[1]]
                    await self.instance.chat('$s$FFF// $FE0{}{}: {}  $FE0+{}'.format(str(pos), suffix, player, times.format_time(rel_time)))
                elif pos == 3:
                    suffix = 'rd'
                    rel_time = self.tournament_times[player] - self.tournament_times[self.tournament_pos[1]]
                    await self.instance.chat('$s$FFF// $FE0{}{}: {}  $FE0+{}'.format(str(pos), suffix, player, times.format_time(rel_time)))
                else:
                    suffix = 'th'
                    rel_time = self.tournament_times[player] - self.tournament_times[self.tournament_pos[1]]
                    await self.instance.chat('$s$FFF// $FE0{}{}: {}  $FE0+{}'.format(str(pos), suffix, player, times.format_time(rel_time)))

                time.sleep(0.75)

    async def rules(self, player, data, **kwargs):
        url_block = ''

        if self.tournament == '':
            await self.instance.chat('$s$FB3Auto$FFFModerator: No tournament in progress.', player)
        else:
            if self.tournament == 'level9':
                url_block = "$FB3$l[https://events.team-apex.eu/level9/]here$l"
            elif self.tournament == 'summit':
                url_block = "$1EF$l[https://events.team-apex.eu/the-summit/]here$l"

            await self.instance.chat('$s$FB3Auto$FFFModerator: You can find the rules for this tournament {}:'
                                     .format(url_block), player)

    async def apexevents_info(self, player, data, **kwargs):
        await self.instance.chat('$s$FFF//$FB3apex$FFFEVENTS $FFFManaging System v$FF00.2.0', player)

        await self.instance.chat('$s$1EF/lvl9rank$FFF: $iGet your current ranking information.', player)
        await self.instance.chat('$s$1EF/rulebook: $iGet some information about the rules of the current tournament.', player)

        if player.level > 0:
            await self.instance.chat('$s$1EF//lvl9start$FFF: $iSetup a new AutoModerator for a LEVEL9 event.', player)
            await self.instance.chat('$s$1EF//lvl9clear$FFF: $iClear an ongoing LEVEL9 event.', player)
   
    async def map_begin(self, map, **kwargs):
        time.sleep(4.5)
        if self.tournament == 'level9' and self.current_map < 9:
            self.current_map += 1
            await self.instance.chat('$s$FFFMap {}/9: {}'.format(self.current_map, map.name))

            all_online = self.instance.player_manager.online
            
            for player in all_online:
                self.map_times[player.nickname] = 0

                if player.nickname in self.tournament_pos.values():
                    player_pos = list(self.tournament_pos.keys())[list(self.tournament_pos.values()).index(player.nickname)]
                    player_total = times.format_time(self.tournament_times[player.nickname])
                    
                    await self.instance.chat('$s$FFF Your current rank: $1EF{}. {}  $1EF{}'
                                             .format(player_pos, player.nickname, player_total), player)
        elif self.tournament == 'level9' and self.current_map == 9:
            await self.show_results()
            self.tournament = ''
    
    async def map_end(self, map, **kwargs):
        if self.tournament == 'level9' and self.current_map > 0:
            for player in self.map_times:
                if self.map_times[player] == 0:
                    self.map_times[player] = map.time_author + 15000

                if player in self.tournament_times:
                    self.tournament_times[player] += self.map_times[player]         # Wenn der Spieler bereits eine Turniergesamtzeit besitzt, addiere die Map-Zeit auf
                else:
                    self.tournament_times[player] = self.tournament_dnf + self.map_times[player]     # Wenn der Spieler noch keine Turniergesamtzeit besitzt, nimm die bisherige DNF-Zeit und addiere die Map-Zeit auf

            for player in self.tournament_times:
                if player not in self.map_times:
                    self.tournament_times[player] += map.time_author + 15000

            self.map_times.clear()
            self.tournament_dnf += map.time_author + 15000
            positions = sorted(self.tournament_times, key=self.tournament_times.get, reverse=False)
            self.tournament_pos = {rank: key for rank, key in enumerate(positions, 1)}
    
    async def player_finish(self, player, race_time, lap_time, lap_cps, race_cps, flow, raw, **kwargs):
        # Weist der aktuellen Map die aktuelle Rundenzeit zu, falls bisherige Bestzeit 0 oder größer als die Rundenzeit.
        if self.tournament == 'level9' and self.current_map > 0:
            async with self.lock:
                if (player.nickname not in self.map_times) or (self.map_times[player.nickname] == 0) or (lap_time < self.map_times[player.nickname]):
                    self.map_times[player.nickname] = lap_time

    async def debug(self, player, data, **kwargs):
        await self.instance.chat('$FFFCurrent ranking: $F00{}'.format(str(self.tournament_pos)), player)

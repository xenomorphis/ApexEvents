import asyncio
import time

from pyplanet.apps.config import AppConfig
from pyplanet.apps.contrib.apexevents.views import EventListView
from pyplanet.contrib.command import Command
from pyplanet.contrib.setting import Setting
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

        self.admin = None
        self.tournament = ''
        self.current_map = -1
        self.map_times = dict()
        self.tournament_players = dict()
        self.tournament_players_amt = 0
        self.tournament_pos = dict()
        self.tournament_times = dict()
        self.tournament_dnf = 0

        self.setting_summit_autodnq_players = Setting(
            'summit_automoderate_players', 'Defines if DNQs should be handled automatically by ApexEvents.', Setting.CAT_BEHAVIOUR, type=bool,
            description='Defines if DNQs should be handled automatically by ApexEvents.',
            default=False,
        )

    async def on_start(self):
        await self.instance.permission_manager.register('manage_event', 'Enables access to the AutoModerator configuration commands.', app=self, min_level=2)
        await self.instance.permission_manager.register('dev', 'Enables access to developer commands.', app=self, min_level=3)

        await self.instance.command_manager.register(
            Command(command='lvl9start', target=self.level9_start, perms='apexevents:manage_event', admin=True,
                    description='Starts the AutoMod-Tool for LEVEL9 events'),
            Command(command='lvl9clear', target=self.level9_clear, perms='apexevents:manage_event', admin=True,
                    description='Resets the AutoMod-Tool for LEVEL9 events'),
            Command(command='lvl9rank', aliases=['lvl9'], target=self.level9_rank, description='Shows current ranking information.')
            .add_param(name="showAll", nargs=1, type=int, required=False, default=0,
                       help="$FB3Use $FFF0 $FB3for displaying only the players around your current position, use $FFF1 $FB3for displaying the complete leaderboard."),
            Command(command='summitstart', target=self.summit_start, perms='apexevents:manage_event', admin=True,
                    description='Starts the AutoMod-Tool for THE SUMMIT'),
            Command(command='summitclear', target=self.summit_clear, perms='apexevents:manage_event', admin=True,
                    description='Resets the AutoMod-Tool for THE SUMMIT'),
            Command(command='rulebook', target=self.rules, description='Shows link to the rules for the current tournament.'),
            Command(command='apexevents', target=self.apexevents_info),
            Command(command='aedebug', target=self.debug, perms='apexevents:dev', admin=True)
        )

        self.context.signals.listen(mp_signals.map.map_begin, self.map_begin)
        self.context.signals.listen(mp_signals.flow.podium_start, self.podium_start)
        self.context.signals.listen(mp_signals.map.map_end, self.map_end)
        self.context.signals.listen(tm_signals.finish, self.player_finish)
        self.context.signals.listen(tm_signals.scores, self.scores)
        self.context.signals.listen(tm_signals.warmup_end, self.warmup_end)

        await self.context.setting.register(self.setting_summit_autodnq_players)

    async def level9_start(self, player, data, **kwargs):
        if self.tournament == '':
            self.tournament = 'level9'
            self.admin = player
            self.map_times.clear()
            self.tournament_times.clear()
            self.tournament_dnf = 0

            current_script = (await self.instance.mode_manager.get_current_script()).lower()
            if 'timeattack' in current_script:
                self.current_map = 0
                await self.instance.command_manager.execute(player, '//modesettings', 'S_TimeLimit', str(540))
            else:
                self.current_map = -1
                await self.instance.command_manager.execute(player, '//mode', 'ta')

            await self.instance.command_manager.execute(player, '//modesettings', 'S_ChatTime', str(20))
            await self.instance.command_manager.execute(player, '//modesettings', 'S_WarmUpNb', str(0))

    async def summit_start(self, player, data, **kwargs):
        if self.tournament == '':
            self.tournament = 'summit'
            self.admin = player
            self.tournament_players_amt = 0
            self.tournament_players.clear()

            current_script = (await self.instance.mode_manager.get_current_script()).lower()
            if 'rounds' in current_script:
                self.current_map = 0
                await self.instance.command_manager.execute(player, '//modesettings', 'S_PointsLimit', str(115))
                await self.instance.command_manager.execute(player, '//modesettings', 'S_FinishTimeout', str(15))
            else:
                self.current_map = -1
                await self.instance.command_manager.execute(player, '//mode', 'rounds')

            await self.instance.command_manager.execute(player, '//modesettings', 'S_ChatTime', str(25))
            await self.instance.command_manager.execute(player, '//modesettings', 'S_WarmUpNb', str(2))
            await self.instance.command_manager.execute(player, '//pointsrepartition', str(28), str(24), str(20), str(17),
                                                        str(14), str(12), str(10), str(9), str(8), str(7), str(6), str(5),
                                                        str(4), str(3), str(2), str(1), str(0), str(0), str(0), str(0),
                                                        str(0), str(0), str(0), str(0), str(0))

    async def level9_clear(self, player, data, **kwargs):
        if self.tournament == 'level9':
            self.tournament = ''

            self.current_map = -1
            self.map_times.clear()
            self.tournament_times.clear()
            self.tournament_dnf = 0

            await self.instance.chat('$s$FB3Auto$FFFModerator: Tournament successfully cleared!', player)

    async def summit_clear(self, player, data, **kwargs):
        if self.tournament == 'summit':
            self.tournament = ''
            self.admin = None
            self.current_map = -1
            self.tournament_players_amt = 0
            self.tournament_players.clear()
            await self.instance.chat('$s$FB3Auto$FFFModerator: Tournament successfully cleared!', player)

    async def level9_rank(self, player, data, **kwargs):
        if data.showAll == 0:
            if player.nickname in self.tournament_pos.values():
                player_pos = list(self.tournament_pos.keys())[list(self.tournament_pos.values()).index(player.nickname)]
                player_total = self.tournament_times[player.nickname]

                if player_pos > 1:
                    player_prev = self.tournament_pos[player_pos - 1]
                    player_prev_total = self.tournament_times[player_prev]
                    time_diff = abs(player_prev_total - player_total)
                    await self.instance.chat('$s$FFF Next rank ahead: $FE0{}. {}  $FE0-{}'
                                            .format((player_pos - 1), player_prev, times.format_time(time_diff)), player)

                await self.instance.chat('$s$FFF Your current rank: $1EF{}. {}  $1EF{}'
                                        .format(player_pos, player.nickname, times.format_time(self.tournament_times[player.nickname])), player)

                if player_pos < len(self.tournament_pos):
                    player_next = self.tournament_pos[player_pos + 1]
                    player_next_total = self.tournament_times[player_next]
                    time_diff = abs(player_next_total - player_total)
                    await self.instance.chat('$s$FFF Next rank behind: $FE0{}. {}  $FE0+{}'
                                            .format((player_pos + 1), player_next, times.format_time(time_diff)), player)
            else:
                await self.instance.chat('$s$FFF You don\'t have a tournament ranking yet. Finish a map to get one.', player)
        else:
            await self.show_results(player)

    async def show_results(self, target='all'):
        if (self.tournament == 'level9' and self.current_map > 1) or self.current_map == 10:
            view = EventListView(self)

            if target == 'all':
                await view.display()
            else:
                await view.display(player=target.login)

        elif self.tournament == 'level9' and self.current_map < 2:
            await self.instance.chat(
                '$s$FB3Auto$FFFModerator: We don\'t have a tournament leaderboard yet. Wait until the next map :)')

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
        await self.instance.chat('$s$FFF//$FB3apex$FFFEVENTS Managing System v$FF00.4.0', player)

        if self.tournament == 'level9' or self.current_map == 10:
            await self.instance.chat('$s$1EF/lvl9$FFF: $iGet your current ranking information.', player)
            await self.instance.chat('$s$1EF/lvl9 1$FFF: $iGet the complete leaderboard.', player)

        await self.instance.chat('$s$1EF/rulebook$FFF: $iGet some information about the rules of the current tournament.', player)

        if player.level > 1:
            if self.tournament == '':
                await self.instance.chat('$s$1EF//lvl9start$FFF: $iSetup a new AutoModerator for a LEVEL9 event.', player)
                await self.instance.chat('$s$1EF//summitstart$FFF: $iSetup a new AutoModerator for THE SUMMIT.', player)

            await self.instance.chat('$s$1EF//lvl9clear$FFF: $iClear an ongoing LEVEL9 event.', player)
            await self.instance.chat('$s$1EF//summitclear$FFF: $iClear an ongoing SUMMIT event.', player)

    async def map_begin(self, map, **kwargs):
        if self.current_map > -1:
            time.sleep(5)

        if self.tournament == 'level9':
            self.current_map += 1

            if self.current_map < 10:
                if self.current_map == 0:
                    await self.instance.command_manager.execute(self.admin, '//modesettings', 'S_TimeLimit', str(540))
                    self.current_map += 1
                    time.sleep(6)

                await self.instance.chat('$s$FFFMap {}/9: {}'.format(self.current_map, map.name))

                all_online = self.instance.player_manager.online

                for player in all_online:
                    self.map_times[player.nickname] = 0

                    if player.nickname in self.tournament_pos.values():
                        player_pos = list(self.tournament_pos.keys())[list(self.tournament_pos.values()).index(player.nickname)]
                        player_total = times.format_time(self.tournament_times[player.nickname])

                        await self.instance.chat('$s$FFF Your current rank: $1EF{}. {}  $1EF{}'
                                                 .format(player_pos, player.nickname, player_total), player)
            elif self.current_map == 10:
                await self.show_results()
                self.tournament = ''

        elif self.tournament == 'summit':
            self.current_map += 1

            if self.current_map < 4:
                if self.current_map == 0:
                    await self.instance.command_manager.execute(self.admin, '//modesettings', 'S_PointsLimit', str(115))
                    await self.instance.command_manager.execute(self.admin, '//modesettings', 'S_FinishTimeout', str(15))
                    self.current_map += 1
                    time.sleep(6)

                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFPreliminary Round {}/3'.format(self.current_map))
                if self.tournament_players_amt > 12:
                    await self.instance.chat('$s$1EFQualification condition: $FFFBe upon the Top 12 players with the most total points after Map 3.')
            elif self.current_map == 4:
                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFElimination Round 1')
                if self.tournament_players_amt > 12:
                    await self.instance.chat('$s$1EFEliminations: $FFFLast two players at the end of this map.')
            elif self.current_map == 5:
                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFElimination Round 2')
                if self.tournament_players_amt > 12:
                    await self.instance.chat('$s$1EFEliminations: $FFFLast two players at the end of this map.')
            elif self.current_map == 6:
                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFSemi-Final')
                if self.tournament_players_amt > 12:
                    await self.instance.chat('$s$1EFEliminations: $FFFLast player per run starting with the fourth run.')
            elif self.current_map == 7:
                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFFinal')

    async def podium_start(self, *args, **kwargs):
        if self.tournament == 'level9':
            if self.current_map < 1:
                time.sleep(5)
                await self.instance.chat(
                    '$s$FB3Auto$FFFModerator: Good Evening and welcome to another $FB3LEVEL9 $FFFtournament! GLHF!')

        elif self.tournament == 'summit':
            online = self.instance.player_manager.online_logins
            auto_dnq = self.setting_summit_autodnq_players.get_value()

            if self.current_map < 1:
                time.sleep(5)
                await self.instance.chat('$s$1EFAuto$FFFModerator: Get ready for... $16FTH$18FE S$1AFU$1BFM$1CFM$1DFI$1EFT')
            elif self.current_map < 3:
                time.sleep(5)
                if len(self.tournament_pos) > 17:
                    player_ref = self.tournament_pos[14]
                    points_ref = self.tournament_players[player_ref]
                    position_ref = 14
                elif len(self.tournament_pos) > 12:
                    player_ref = self.tournament_pos[12]
                    points_ref = self.tournament_players[player_ref]
                    position_ref = 12

                for player in self.tournament_players.keys():
                    if len(self.tournament_pos) > 12:
                        diff_to_q = self.tournament_players[player] - points_ref
                        if diff_to_q > 0:
                            colorcode = '$3C0+'
                        else:
                            colorcode = '$F30'

                        await self.instance.chat('$s$1EFPRELIMINARIES | $FFFYour total points: $FE0{} $FFF(Diff to P{}: {}{}$FFF)'
                                                 .format(str(self.tournament_players[player]), str(position_ref), colorcode, str(diff_to_q)), player)
                    else:
                        player_pos = list(self.tournament_pos.keys())[list(self.tournament_pos.values()).index(player)]
                        await self.instance.chat('$s$1EFPRELIMINARIES | $FFFYour total points: $FE0{} $FFF(Pos $FE0{}$FFF)'
                                                 .format(str(self.tournament_players[player]), str(player_pos)), player)
            elif self.current_map == 3:
                time.sleep(2.5)
                if len(self.tournament_pos) > 17:
                    player_ref = self.tournament_pos[14]
                    points_ref = self.tournament_players[player_ref]
                    position_ref = 14
                elif len(self.tournament_pos) > 12:
                    player_ref = self.tournament_pos[12]
                    points_ref = self.tournament_players[player_ref]
                    position_ref = 12

                for player in self.tournament_players.keys():
                    if len(self.tournament_pos) > 12:
                        diff_to_q = self.tournament_players[player] - points_ref
                        if diff_to_q > 0:
                            colorcode = '$3C0+'
                        else:
                            colorcode = '$F30'

                        await self.instance.chat('$s$1EFPRELIMINARIES | $FFFYour total points: $FE0{} $FFF(Diff to P{}: {}{}$FFF)'
                                                 .format(str(self.tournament_players[player]), str(position_ref), colorcode, str(diff_to_q)), player)
                    else:
                        player_pos = list(self.tournament_pos.keys())[list(self.tournament_pos.values()).index(player)]
                        await self.instance.chat('$s$1EFPRELIMINARIES | $FFFYour total points: $FE0{} $FFF(Pos $FE0{}$FFF)'
                                                 .format(str(self.tournament_players[player]), str(player_pos)), player)

                time.sleep(5)
                players_current = len(self.tournament_pos)
                if players_current > 17:
                    await self.instance.chat('$s$1EFPRELIMINARIES | $FFFDNQ\'ed players:')
                    for i in range(players_current, 14, -1):
                        player_login_out = self.tournament_pos[i]
                        if player_login_out in online:
                            player_out = self.instance.player_manager.get_player(player_login_out)
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_out.nickname))
                            if auto_dnq:
                                await self.instance.command_manager.execute(self.admin, '//forcespec', player_login_out)
                        else:
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_login_out))

                        del self.tournament_players[player_login_out]
                elif players_current > 12:
                    await self.instance.chat('$s$1EFPRELIMINARIES | $FFFDNQ\'ed players:')
                    for i in range(players_current, 12, -1):
                        player_login_out = self.tournament_pos[i]
                        if player_login_out in online:
                            player_out = self.instance.player_manager.get_player(player_login_out)
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_out.nickname))
                            if auto_dnq:
                                await self.instance.command_manager.execute(self.admin, '//forcespec', player_login_out)
                        else:
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_login_out))

                        del self.tournament_players[player_login_out]
            elif self.current_map == 4:
                time.sleep(7.5)
                players_current = len(self.tournament_pos)
                if players_current > 13:
                    await self.instance.chat('$s$1EFELIMINATION 1 | $FFFDNQ\'ed players:')
                    for i in range(players_current, 11, -1):
                        player_login_out = self.tournament_pos[i]
                        if player_login_out in online:
                            player_out = self.instance.player_manager.get_player(player_login_out)
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_out.nickname))
                            if auto_dnq:
                                await self.instance.command_manager.execute(self.admin, '//forcespec', player_login_out)
                        else:
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_login_out))

                        del self.tournament_players[player_login_out]
                elif players_current > 10:
                    await self.instance.chat('$s$1EFELIMINATION 1 | $FFFDNQ\'ed players:')
                    for i in range(players_current, 10, -1):
                        player_login_out = self.tournament_pos[i]
                        if player_login_out in online:
                            player_out = self.instance.player_manager.get_player(player_login_out)
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_out.nickname))
                            if auto_dnq:
                                await self.instance.command_manager.execute(self.admin, '//forcespec', player_login_out)
                        else:
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_login_out))

                        del self.tournament_players[player_login_out]
            elif self.current_map == 5:
                time.sleep(7.5)
                players_current = len(self.tournament_pos)
                if players_current > 8:
                    await self.instance.chat('$s$1EFELIMINATION 2 | $FFFDNQ\'ed players:')
                    for i in range(players_current, 8, -1):
                        player_login_out = self.tournament_pos[i]
                        if player_login_out in online:
                            player_out = self.instance.player_manager.get_player(player_login_out)
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_out.nickname))
                            if auto_dnq:
                                await self.instance.command_manager.execute(self.admin, '//forcespec', player_login_out)
                        else:
                            await self.instance.chat('$s$1EFRank {}: $FFF{}'.format(str(i), player_login_out))

                        del self.tournament_players[player_login_out]

    async def map_end(self, map, **kwargs):
        if self.tournament == 'level9':
            if self.current_map > 0:
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
        if self.tournament == 'level9' and self.current_map > 0:
            async with self.lock:
                if (player.nickname not in self.map_times) or (self.map_times[player.nickname] == 0) or (lap_time < self.map_times[player.nickname]):
                    self.map_times[player.nickname] = lap_time

    async def scores(self, section, players, **kwargs):
        if self.tournament == 'summit':
            if 0 < self.current_map < 4:
                if section == 'EndMap':
                    for player in players:
                        if ('map_points' in player) and (player['player'].login in self.tournament_players):
                            self.tournament_players[player['player'].login] += player['map_points']

                    positions = sorted(self.tournament_players, key=self.tournament_players.get, reverse=True)
                    self.tournament_pos = {rank: key for rank, key in enumerate(positions, 1)}
            elif self.current_map > 3:
                if section == 'EndMap':
                    for player in players:
                        if ('map_points' in player) and (player['player'].login in self.tournament_players):
                            self.tournament_players[player['player'].login] = player['map_points']

                    positions = sorted(self.tournament_players, key=self.tournament_players.get, reverse=True)
                    self.tournament_pos = {rank: key for rank, key in enumerate(positions, 1)}

    async def warmup_end(self):
        if self.tournament == 'summit' and self.current_map == 1:
            await self.instance.command_manager.execute(self.admin, '//srvpass', 'awas')
            self.tournament_players_amt = self.instance.player_manager.count_players
            participants = self.instance.player_manager.online_logins

            for player in participants:
                self.tournament_players[player] = 0

    async def debug(self, player, data, **kwargs):
        await self.instance.chat('$FFFCurrent ranking ({}): $F00{}'.format(len(self.tournament_pos), str(self.tournament_pos)), player)
        if self.tournament == 'summit' and self.current_map > 1:
            await self.instance.chat('$FFFPlayer amount at start: $F00{}'.format(str(self.tournament_players_amt)), player)
            await self.instance.chat('$FFFPlayers in tournament: $F00{}'.format(str(self.tournament_players)), player)
            await self.instance.chat('$FFFPlayers online: $F00{}'.format(str(self.instance.player_manager.online_logins)), player)

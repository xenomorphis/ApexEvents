import asyncio
from datetime import date
import time

from pyplanet.apps.config import AppConfig
from .views import EventToolbarView, Lvl9ListView, SummitListView
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
        self.current_run = 1
        self.is_warmup = False
        self.map_times = dict()
        self.finished_maps = dict()
        self.tournament_day = ''
        self.tournament_locked = False
        self.tournament_player_names = dict()
        self.tournament_players = dict()
        self.tournament_players_amt = 0
        self.tournament_pos = dict()
        self.tournament_times = dict()
        self.tournament_dnf = 0

        self.tournament_widget = EventToolbarView(self)

        self.setting_summit_autodnq_players = Setting(
            'summit_automoderate_players', 'Defines if DNQs should be handled automatically by ApexEvents.', Setting.CAT_BEHAVIOUR, type=bool,
            description='Defines if DNQs should be handled automatically by ApexEvents.', default=False,
        )

        self.setting_summit_finish_timeout = Setting(
            'summit_finish_timeout', 'Defines the amount of time left to finish a map (in seconds).',
            Setting.CAT_BEHAVIOUR, type=int,
            description='Defines the amount of time left to finish a map (in seconds).', default=15,
        )

    async def on_start(self):
        await self.instance.permission_manager.register('manage_event', 'Enables access to the AutoModerator configuration commands.', app=self, min_level=2)
        await self.instance.permission_manager.register('dev', 'Enables access to developer commands.', app=self, min_level=3)

        await self.instance.command_manager.register(
            Command(command='lvl9start', target=self.level9_start, perms='apexevents:manage_event', admin=True,
                    description='Starts the AutoMod-Tool for LEVEL9 events'),
            Command(command='lvl9clear', target=self.level9_clear, perms='apexevents:manage_event', admin=True,
                    description='Resets the AutoMod-Tool for LEVEL9 events'),
            Command(command='lvl9rank', aliases=['lvl9'], target=self.level9_rank,
                    description='Shows current ranking information.'),
            Command(command='summitstart', target=self.summit_start, perms='apexevents:manage_event', admin=True,
                    description='Starts the AutoMod-Tool for THE SUMMIT')
            .add_param(name="mode", nargs=1, type=str, required=False, default='', help="Use 'test' for starting a SUMMIT test session."),
            Command(command='summitclear', target=self.summit_clear, perms='apexevents:manage_event', admin=True,
                    description='Resets the AutoMod-Tool for THE SUMMIT'),
            Command(command='summitrank', aliases=['summit'], target=self.summit_rank,
                    description='Shows current ranking information.'),
            Command(command='rulebook', target=self.rules,
                    description='Shows link to the rules for the current tournament.'),
            Command(command='apexevents', target=self.apexevents_info),
            Command(command='aedebug', target=self.debug, perms='apexevents:dev', admin=True)
        )

        self.context.signals.listen(mp_signals.map.map_begin, self.map_begin)
        self.context.signals.listen(mp_signals.flow.podium_start, self.podium_start)
        self.context.signals.listen(mp_signals.map.map_end, self.map_end)
        self.context.signals.listen(tm_signals.finish, self.player_finish)
        self.context.signals.listen(tm_signals.scores, self.scores)
        self.context.signals.listen(tm_signals.warmup_end, self.warmup_end)
        self.context.signals.listen(tm_signals.warmup_start, self.warmup_start)

        await self.context.setting.register(self.setting_summit_autodnq_players, self.setting_summit_finish_timeout)
        await self.instance.chat('$s$FFF//$FB3apex$FFFEVENTS Management System v$FF00.5.0 online')

    async def level9_start(self, player, data, **kwargs):
        if self.tournament == '':
            self.tournament = 'level9'
            self.tournament_day = date.today()
            self.admin = player
            self.map_times.clear()
            self.finished_maps.clear()
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
            if data.mode == 'test':
                self.tournament = 'summit_test'
            else:
                self.tournament = 'summit'

            self.tournament_locked = False
            self.admin = player
            self.current_run = 1
            self.tournament_players_amt = 0
            self.tournament_player_names.clear()
            self.tournament_players.clear()
            self.tournament_pos.clear()

            current_script = (await self.instance.mode_manager.get_current_script()).lower()
            timeout = await self.setting_summit_finish_timeout.get_value()

            if 'rounds' in current_script:
                self.current_map = 0
                await self.instance.command_manager.execute(player, '//modesettings', 'S_PointsLimit', str(115))
                await self.instance.command_manager.execute(player, '//modesettings', 'S_FinishTimeout', str(timeout))
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
            self.finished_maps.clear()
            self.tournament_times.clear()
            self.tournament_dnf = 0

            await self.tournament_widget.hide()
            await self.instance.chat('$s$FB3Auto$FFFModerator: Tournament successfully cleared!', player)

    async def summit_clear(self, player, data, **kwargs):
        if self.tournament in ['summit', 'summit_test']:
            self.tournament_locked = False
            self.current_map = -1
            self.current_run = 1
            self.tournament_players_amt = 0
            self.tournament_player_names.clear()
            self.tournament_players.clear()
            self.tournament_pos.clear()

            await self.tournament_widget.hide()

            if self.tournament == 'summit':
                await self.instance.chat('$s$FB3Auto$FFFModerator: Tournament successfully cleared!', player)
                await self.instance.command_manager.execute(self.admin, '//srvpass')
            else:
                await self.instance.chat('$s$FB3Auto$FFFModerator: SUMMIT test mode deactivated!', player)

            self.admin = None
            self.tournament = ''

    async def level9_rank(self, player, data, **kwargs):
        if ('level9' in self.tournament and len(self.tournament_times) > 0) or self.current_map == 10:
            view = Lvl9ListView(self, player.nickname)
            await view.display(player.login)
        elif 'level9' in self.tournament and len(self.tournament_times) == 0:
            await self.instance.chat(
                '$s$FB3Auto$FFFModerator: We don\'t have a tournament leaderboard yet. Wait until the next map :)',
                player)

    async def summit_rank(self, player, data, **kwargs):
        if (self.tournament_locked and self.tournament == 'summit' and self.current_map < 4) or self.tournament == 'summit_test':
            view = SummitListView(self, player.login)
            await view.display(player.login)
        elif self.tournament == 'summit' and self.current_map == 1 and not self.tournament_locked:
            await self.instance.chat(
                '$s$1EFAuto$FFFModerator: We don\'t have a tournament leaderboard yet. Wait until the warmup has ended.', player)
        elif self.tournament == 'summit' and self.current_map > 3:
            await self.instance.chat(
                '$s$1EFAuto$FFFModerator: This command is only available during the Preliminary Round.', player)

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
        await self.instance.chat('$s$FFF//$FB3apex$FFFEVENTS Managing System v$FF00.5.1-0', player)

        if self.tournament == 'level9' or self.current_map == 10:
            await self.instance.chat('$s$1EF/lvl9$FFF: $iGet the current leaderboard (updated after each map).', player)

        await self.instance.chat('$s$1EF/rulebook$FFF: $iGet some information about the rules of the current tournament.', player)

        if player.level > 1:
            if self.tournament == '':
                await self.instance.chat('$s$1EF//lvl9start$FFF: $iSetup a new AutoModerator for a LEVEL9 event.', player)
                await self.instance.chat('$s$1EF//summitstart$FFF: $iSetup a new AutoModerator for THE SUMMIT.', player)

                if player.level > 2:
                    await self.instance.chat(
                        '$s$1EF//summitstart test$FFF: $iSetup the AutoModerator in SUMMIT test mode.', player)

            await self.instance.chat('$s$1EF//lvl9clear$FFF: $iClear an ongoing LEVEL9 event.', player)
            await self.instance.chat('$s$1EF//summitclear$FFF: $iClear an ongoing SUMMIT event.', player)

    async def map_begin(self, map, **kwargs):
        current_players = self.instance.player_manager.count_players

        if self.current_map > -1:
            time.sleep(5)

        if self.tournament == 'level9':
            self.current_map += 1

            if self.current_map < 10:
                if self.current_map == 0:
                    await self.instance.command_manager.execute(self.admin, '//modesettings', 'S_TimeLimit', str(540))
                    self.current_map += 1
                    time.sleep(6)

                if self.current_map == 2:
                    await self.tournament_widget.display()

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
                await self.instance.chat('$s$FFFThe tournament has concluded. You can view the final results via the '
                                         'command $FB1/lvl9$FFF. Thx for playing and see \'ya next time!')
                self.tournament = 'level9-ended'

        elif self.tournament == 'level9-ended':
            await self.tournament_widget.hide()
            self.tournament = ''

        elif self.tournament == 'summit':
            self.current_map += 1
            qualified = 0
            message_condition = ' at the end of the map'

            if self.current_map < 4:
                if self.current_map == 0:
                    timeout = await self.setting_summit_finish_timeout.get_value()

                    await self.instance.command_manager.execute(self.admin, '//modesettings', 'S_PointsLimit', str(115))
                    await self.instance.command_manager.execute(self.admin, '//modesettings', 'S_FinishTimeout', str(timeout))
                    self.current_map += 1
                    time.sleep(6)

                if self.current_map == 1:
                    await self.tournament_widget.display()

                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFPreliminary Round {}/3'.format(self.current_map))
                message_condition = ' with the most total points after Map 3'

                if self.tournament_players_amt > 17:
                    qualified = 14
                else:
                    qualified = 12

            elif self.current_map == 4:
                await self.tournament_widget.hide()
                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFElimination Round 1')

                if current_players > 13:
                    qualified = 11
                else:
                    qualified = 10

            elif self.current_map == 5:
                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFElimination Round 2')
                qualified = 8

            elif self.current_map == 6:
                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFSemi-Final')

                if current_players > 8:
                    await self.instance.chat(
                        '$s$1EFEliminations: $FFFLast player per run starting with the fourth run. A maximum of 6'
                        'players will advance to the final.')
                else:
                    await self.instance.chat(
                        '$s$1EFEliminations: $FFFLast player per run starting with the fourth run.')

            elif self.current_map == 7:
                await self.instance.chat('$s$1EFTHE SUMMIT: $FFFFinal')

            else:
                self.tournament_locked = False
                self.tournament = ''
                await self.instance.command_manager.execute(self.admin, '//srvpass')

            if qualified > 0:
                await self.instance.chat('$s$1EFQualification condition: $FFFBe upon the Top {} players{}.'
                                         .format(str(qualified), message_condition))

        elif self.tournament == 'summit_test':
            self.current_map += 1

    async def podium_start(self, *args, **kwargs):
        if self.tournament == 'level9':
            if self.current_map < 1:
                time.sleep(5)
                await self.instance.chat(
                    '$s$FB3Auto$FFFModerator: Good Evening and welcome to another $FB3LEVEL9 $FFFtournament! GLHF!')

        elif self.tournament == 'summit':
            online = self.instance.player_manager.online_logins
            auto_dnq = await self.setting_summit_autodnq_players.get_value()

            if self.current_map < 1:
                time.sleep(5)
                await self.instance.chat('$s$1EFAuto$FFFModerator: Get ready for... $16FTH$18FE S$1AFU$1BFM$1CFM$1DFI$1EFT')
            elif self.current_map < 7:
                players_current = len(self.tournament_pos)

                if self.current_map < 4:
                    dnq_message = '$s$1EFPRELIMINARIES | '

                    if players_current > 17:
                        player_ref = self.tournament_pos[14]
                        qualified = 14
                    else:
                        player_ref = self.tournament_pos[12]
                        qualified = 12

                    points_ref = self.tournament_players[player_ref]
                    time.sleep(2.5)

                    for player in self.tournament_players:
                        if players_current > qualified:
                            p_diff = self.tournament_players[player] - points_ref

                            if p_diff > 0:
                                colorcode = '$3C0+'
                            else:
                                colorcode = '$F30'

                            await self.instance.chat('{}$FFFYour total points: $FE0{} $FFF(Diff to P{}: {}{}$FFF)'
                                                     .format(dnq_message, str(self.tournament_players[player]),
                                                             str(qualified), colorcode, str(p_diff)), player)
                        else:
                            player_pos = list(self.tournament_pos.keys())[list(self.tournament_pos.values()).index(player)]
                            await self.instance.chat('{}$FFFYour total points: $FE0{} $FFF(Pos $FE0{}$FFF)'
                                                     .format(dnq_message, str(self.tournament_players[player]), str(player_pos)), player)

                    if self.current_map < 3:
                        qualified = 99

                elif self.current_map == 4:
                    dnq_message = '$s$1EFELIMINATION 1 | '

                    if players_current > 13:
                        qualified = 11
                    else:
                        qualified = 10

                elif self.current_map == 5:
                    dnq_message = '$s$1EFELIMINATION 2 | '
                    qualified = 8
                else:
                    dnq_message = '$s$1EFSEMI-FINAL | '
                    qualified = 6

                if players_current > qualified:
                    time.sleep(5)
                    await self.instance.chat('{}$FFFDNQ\'ed players:'.format(dnq_message))

                    for i in range(players_current, qualified, -1):
                        dnq_player = self.tournament_pos[i]

                        if self.tournament_players[dnq_player] == self.tournament_players[self.tournament_pos[qualified]]:
                            await self.instance.chat('$s$1EFNo further eliminations because of tied ranks.')
                            break

                        if (dnq_player in online) and auto_dnq:
                            await self.instance.command_manager.execute(self.admin, '//forcespec', dnq_player)

                        await self.instance.chat('$s$1EFRank {}: $FFF{}'
                                                 .format(str(i), self.tournament_player_names[dnq_player]))
                        del self.tournament_players[dnq_player]
                        time.sleep(0.75)

    async def map_end(self, map, **kwargs):
        if self.tournament == 'level9':
            if self.current_map > 0:
                for player in self.map_times:
                    if self.map_times[player] == 0:
                        self.map_times[player] = map.time_author + 15000
                    else:
                        self.finished_maps[player] += 1

                    if player in self.tournament_times:
                        self.tournament_times[player] += self.map_times[player]
                    else:
                        self.tournament_times[player] = self.tournament_dnf + self.map_times[player]

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
                if player.nickname not in self.finished_maps:
                    self.finished_maps[player.nickname] = 0

                if (player.nickname not in self.map_times) or (self.map_times[player.nickname] == 0) or (lap_time < self.map_times[player.nickname]):
                    self.map_times[player.nickname] = lap_time

    async def scores(self, section, players, **kwargs):
        if self.tournament == 'summit':
            if self.current_map in [1, 2, 3, 6]:
                if section == 'PreEndRound' and not self.is_warmup:
                    for player in players:
                        if ('round_points' in player) and (player['player'].login in self.tournament_players):
                            self.tournament_players[player['player'].login] += player['round_points']

                    positions = sorted(self.tournament_players, key=self.tournament_players.get, reverse=True)
                    self.tournament_pos = {rank: key for rank, key in enumerate(positions, 1)}

                    if self.current_map == 6:
                        rank = len(self.tournament_pos)

                        if self.current_run > 3 and rank > 4:
                            dnq_player = self.tournament_pos[rank]

                            if self.tournament_players[dnq_player] == self.tournament_players[self.tournament_pos[rank - 1]]:
                                await self.instance.chat('$s$1EFNo elimination this run because of tied ranks.')
                            else:
                                online = self.instance.player_manager.online_logins
                                auto_dnq = await self.setting_summit_autodnq_players.get_value()
                                await self.instance.chat('$s$1EFSEMI-FINAL | $FFFDNQ\'ed player:')

                                if (dnq_player in online) and auto_dnq:
                                    await self.instance.command_manager.execute(self.admin, '//forcespec', dnq_player)

                                await self.instance.chat(
                                    '$s$1EFRank {}: $FFF{}'.format(str(rank), self.tournament_player_names[dnq_player]))
                                del self.tournament_players[dnq_player]

                        self.current_run += 1

            elif self.current_map > 3:
                if section == 'EndMap':
                    for player in players:
                        if ('map_points' in player) and (player['player'].login in self.tournament_players):
                            self.tournament_players[player['player'].login] = player['map_points']

                    positions = sorted(self.tournament_players, key=self.tournament_players.get, reverse=True)
                    self.tournament_pos = {rank: key for rank, key in enumerate(positions, 1)}

        if self.tournament == 'summit_test' and self.current_map > 0:
            if section == 'PreEndRound' and not self.is_warmup:
                for player in players:
                    if ('round_points' in player) and (player['player'].login in self.tournament_players):
                        self.tournament_players[player['player'].login] += player['round_points']

                positions = sorted(self.tournament_players, key=self.tournament_players.get, reverse=True)
                self.tournament_pos = {rank: key for rank, key in enumerate(positions, 1)}
                await self.debug(self.admin, '')

    async def warmup_start(self):
        self.is_warmup = True

    async def warmup_end(self):
        self.is_warmup = False

        if self.tournament in ['summit', 'summit_test'] and self.current_map == 1 and not self.tournament_locked:
            self.tournament_locked = True

            if self.tournament == 'summit':
                await self.instance.command_manager.execute(self.admin, '//srvpass', 'awas')

            self.tournament_players_amt = self.instance.player_manager.count_players
            participants = self.instance.player_manager.online_logins
            pseudo_pos = 1

            for player in participants:
                self.tournament_players[player] = 0
                self.tournament_pos[pseudo_pos] = player
                player_object = await self.instance.player_manager.get_player(player)
                self.tournament_player_names[player] = player_object.nickname
                pseudo_pos += 1

        if self.tournament == 'summit' and self.current_map == 6:
            for player in self.tournament_players:
                self.tournament_players[player] = 0

    async def debug(self, player, data, **kwargs):
        await self.instance.chat('$FFFCurrent ranking ({}): $F00{}'.format(len(self.tournament_pos), str(self.tournament_pos)), player)
        if self.tournament == 'summit' and self.current_map > 1:
            await self.instance.chat('$FFFPlayer amount at start: $F00{}'.format(str(self.tournament_players_amt)), player)
            await self.instance.chat('$FFFPlayers in tournament: $F00{}'.format(str(self.tournament_players)), player)
            await self.instance.chat('$FFFPlayers online: $F00{}'.format(str(self.instance.player_manager.online_logins)), player)

==========
ApexEvents
==========

Changelog
-----------
``0.5.1``
    | Update: [SUMMIT] Introduces rules to deal with ties during the semi-final
    | Update: [SUMMIT] Simplifies AutoMod message generation on map_begin
    | Update: [SUMMIT] Simplifies DNQ logic
    | Update: [LEVEL9] Simplifies leaderboard generation
    | Fix: [LEVEL9] Stops idle players from being included in the leaderboard

``0.5.0``
    | Feature: [GENERAL] Adds tournament toolbar
    | Update: [SUMMIT] Adds DNQ logic for SUMMIT semi-finals
    | Update: [SUMMIT] Adds a user interface used for displaying the current leaderboard during the
      SUMMIT preliminaries
    | Update: [SUMMIT] Adds a configuration option for adjusting the finish timeout
    | Update: [SUMMIT] Improves the AutoModerator chat messages
    | Update: [SUMMIT] Automatically remove the server password when clearing the tournament
    | Update: [LEVEL9] Removes chat-based leaderboard information available via the ``/lvl9rank`` command
    | Fix: [SUMMIT] Missing ``await`` statements when using coroutines from the player_manager class
    | Fix: [SUMMIT] Inaccessible settings values due to missing ``await`` statements
    | Fix: [LEVEL9] Players disconnecting during the tournament get their 'maps_finished' counter resetted
      if they rejoin on a later map

``0.4.2``
    | Update: [LEVEL9] Adds the new column 'maps_finished' to the leaderboard UI

``0.4.1``
    | Feature: [LEVEL9] Adds a clean UI to the output of the complete leaderboard
    | Update: [LEVEL9] Adds a 'tournament concluded' chat message
    | Update: [GENERAL] Code cleanup

``0.4.0``
    | Feature: [SUMMIT] Adds basic support for 'THE SUMMIT' event mode
    | Fix: [LEVEL9] Typo in function call ``Command.add_params``
    | Fix: [LEVEL9] ``show_results`` skips last leaderboard record

``0.3.5``
    | Update: [LEVEL9] Modifies ``/lvl9rank`` command for getting the entire leaderboard via an
      optional argument
    | Update: [GENERAL] Code cleanup
    | Fix: [LEVEL9] Plugin closes a LEVEL9 event one map earlier than expected

``0.3.0``
    | Feature: Fully supports the 'LEVEL9' event mode

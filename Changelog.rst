==========
ApexEvents
==========

Changelog
-----------
``0.5.0``
    | Update: [SUMMIT] Adds a user interface used for displaying the current leaderboard during the
      SUMMIT preliminaries
    | Update: [SUMMIT] Improves the AutoModerator chat messages
    | Fix: [SUMMIT] Adds missing await statements when using coroutines from the player_manager class

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

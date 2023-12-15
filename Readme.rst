==========
ApexEvents
==========
:Release: 2023-12-20
:Version: 1.0.0

ApexEvents is an Auto-Moderator plugin for `PyPlanet <https://pypla.net/en/latest/index.html>`_ used for managing tournaments and events in TrackMania². It keeps track of the results,
enforces the rules and provides event-specific information to the participants like qualifying conditions or the current leaderboard.


Basic Usage
-----------
ApexEvents provides the following chat commands for interacting with and controlling the plugin:

**Administrative commands**

``//lvl9start``
    | *Admin Level 1*
    | Initializes and starts a new LEVEL9 tournament sequence.

``//lvl9clear``
    | *Admin Level 1*
    | Ends an active LEVEL9 tournament sequence.

``//summitstart``
    | *Admin Level 1*
    | Initializes and starts a SUMMIT tournament sequence.

``//summitclear``
    | *Admin Level 1*
    | Ends an active SUMMIT tournament sequence.

--------

**Development commands**

``//aedebug``
    | *Admin Level 3*
    | Outputs current values of almost every plugin variable. Needed occasionally during the development process. Will be removed once plugin is stable.

--------

**Player commands**

``/lvl9rank``
    | *No permissions needed*
    | Displays the current tournament leaderboard. Only available during a LEVEL9 event.

``/summitrank``
    | *No permissions needed*
    | Displays the current tournament leaderboard. Only available during the preliminary rounds of
      SUMMIT events.

``/rulebook``
    | *No permissions needed*
    | Shows a link to the rules for the current tournament.

``/apexevents``
    | *No permissions needed*
    | Writes the version number and all currently available commands into the ingame chat.

==========
ApexEvents
==========
:Release: 2022-12-20
:Version: 0.5.0

ApexEvents is a plugin for `PyPlanet <https://pypla.net/en/latest/index.html>`_ and provides a management toolbox for the
Trackmania 2 events hosted by Team APEX.


Basic Usage
-----------
ApexEvents is currently a command-line tool using the ingame chat as it's CLI. As it is mainly an administrative tool used
internally for our events there's no user interface planned or necessary.

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
    | Writes extended ranking information of the user into his personal chat or shows the whole current
      leaderboard in a new window. Only available during a LEVEL9 event.

``/summitrank``
    | *No permissions needed*
    | Displays the current tournament leaderboard. Only available during the preliminary rounds of
      SUMMIT events.

``/rulebook``
    | *No permissions needed*
    | Shows a link to the rules for the current tournament.

``/apexevents``
    | *No permissions needed*
    | Writes the version number and all available commands into the ingame chat.

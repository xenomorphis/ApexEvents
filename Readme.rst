==========
ApexEvents
==========
:Developer: apex/xenomorphis
:Version: 0.2.0

ApexEvents is a plugin for `PyPlanet <https://pypla.net/en/latest/index.html>`_ and provides a management toolbox for the
Trackmania 2 events hosted by Team APEX.


Basic Usage
-----------
ApexEvents is currently a command-line tool using the ingame chat as it's CLI. As it is mainly an administrative tool used
internally for our events there's no user interface planned or necessary.

**Administrative commands**

``//lv9start``
    | *Admin Level 1*
    | Initializes and starts a new LEVEL9 tournament sequence.

``//lv9clear``
    | *Admin Level 1*
    | Ends an active LEVEL9 tournament sequence.

--------

**Development commands**

``//aedebug``
    | *Admin Level 3*
    | Outputs current values of almost every plugin variable. Needed occasionally during the development process. Will be removed once plugin is stable.

--------

**Player commands**

``/lv9rank``
    | *No permissions needed*
    | Writes extended ranking information of the user into his personal chat.

``/rulebook``
    | *No permissions needed*
    | Shows a link to the rules for the current tournament.

``/apexevents``
    | *No permissions needed*
    | Writes the version number and all available commands into the ingame chat.


Roadmap
-------
A non-comprehensive list of enhancements planned for future releases. As this is a spare-time project there's no
guarantee that the features listet here will be actually developed. So take it as a collection of ideas how this module could
be improved beyond it's basic functionalities.

* Add support for THE SUMMIT

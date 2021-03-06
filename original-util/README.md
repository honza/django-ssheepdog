ssheepdog
=========

ssheepdog is a public ssh key management tool for teams of programmers.
Different people need different privileges to different servers. Ssheepdog
allows you to specify these relationships in a simple json file and then sync
the keys to the appropriate servers.

Ssheepdog uses [Fabric][1] to make ssh connections and handle hosts.

JSON format
-----------

    {
        "people": {
            "john": "public ssh key",
            "mark": "public ssh key"
        },
        "servers": {
            "user@123.123.123.123": [
                "john",
                "mark"
            ],
            "user2@111.111.111.111:1234": [
                "mark"
            ]
        },
        "last_modified": "2011-11-29 13:00:00"
    }

Commands
--------

    $ python ssheepdog.py
    $ python ssheepdog.py /path/to/data/file

If no path is specified, ssheepdog will look for a file called `data.json` in
the current working directory.

License
-------

TBD

[1]: http://docs.fabfile.org/en/1.3.3/usage/library.html

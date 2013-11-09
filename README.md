# RemoteUnpack
This is a server/client application used for remotley unpacking archives and
reporting back progress to the client. 

Written as a exercise in socket programming.

## Protocol for communication
The server sends and receives data from the socket as serialized JSON.

TODO: Update/write this...
NOTE: The information below is deprecated...

The protocol for communication over the sockets is similar to the HTTP-protocol
but a lot simpler. All headers are whitespace delimited and follow this general form:

`RU/major.minor METHOD ARG [OPT]`

See below for examples

###Valid methods:

####LIST
List the contents of the supplied `URI` directory. This is essentially `ls`

**Example:**
`RU/1.0 LIST /path/to/directory`

* Will return _404 Not Found_ if the directory does not exist
* Will return _401 Unauthorized_ if the directory is unreadable due to permissions 

####UNPACK
Extract the supplied archive `URI` file.

**Example:**
`RU/1.0 UNPACK /path/to/archive.rar /path/to/extract/directory`


* Will return _404 Not Found_ if the archive does not exist.

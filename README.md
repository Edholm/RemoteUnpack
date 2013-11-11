# RemoteUnpack
This is a server/client application used for remotley unpacking archives and
reporting back progress to the client. 

Written as a exercise in socket programming.

## Protocol for communication
The server sends and receives data from the socket as serialized JSON.

TODO: Update/write this...

###Valid methods:

####GET
List the contents of the supplied `URI` directory. This is essentially `ls`


####UNPACK
Extract the supplied archive `URI` file.


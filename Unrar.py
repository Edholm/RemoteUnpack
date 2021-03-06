""" Prepares and processes the unrar command. """
from subprocess import Popen, PIPE, STDOUT
import re
import signal


class Unrar(object):
    """ Defines "Interface" to the unrar shell command."""
    def __init__(self, extract_path):
        self.extract_path = extract_path
        self.regex = re.compile(r'([0-9]{1,3})%')
        self.exit_codes = {
            0:   "Success",
            1:   "Warning",
            2:   "Fatal",
            3:   "CRC mismatch",
            4:   "Lock",
            5:   "Write",
            6:   "Open",
            7:   "User error",
            8:   "Memory",
            9:   "Create",
            10:  "No files to extract",
            11:  "Bad password",
            255: "User break"}

    def extract(self, rarfile, progress_queue):
        """ unrar the supplied file to the path supplied in init.
            The progress is put on the queue as the tuple
            (filename, progress) until unrar exits when the tuple
            ("exit", exitcode) is put in the queue to signal end.
            Returns the exit code of unrar

        """
        import queue
        if not isinstance(progress_queue, queue.Queue):
            raise TypeError("Not a valid queue supplied. Got " +
                            type(progress_queue))
        cmd = self._build_unrar_cmd(rarfile)
        return self._execute(cmd, rarfile, progress_queue)

    def explain_exitcode(self, exitcode):
        """ Lookup the associated phrase with a given exit code. """
        return self.exit_codes[exitcode]

    def _build_unrar_cmd(self, rarfile):
        """ Build the shell command for unrar. """
        cmd = "unrar x -ai -o+ -y -idc "
        cmd = cmd + re.escape(rarfile) + " " + re.escape(self.extract_path)
        from shlex import split
        return split(cmd)

    def _execute(self, unrarcmd, rarfile, progress_queue):
        """ Execute the unrarcmd and prints the parsed progress bar.
            For unrar return codes, see: errhnd.hpp in source code
            Returns the exit code

        """
        from os.path import basename
        filename = basename(rarfile)
        progress = 0
        retcode = 0
        proc = Popen(unrarcmd, stdout=PIPE, stderr=STDOUT)
        try:
            while True:
                retcode = proc.poll()  # None while subprocess is running
                # Using word-for-word for nicer progress output.
                word = _read_word(proc.stdout)
                match = self.regex.search(word)
                if match:
                    progress = int(match.group(1))
                    progress_queue.put((filename, progress))

                if retcode is not None:
                    if retcode == 0:
                        # We'll never match 100% since it is overwritten;
                        # so our workaround is adding one to the progress
                        progress += 1
                        progress_queue.put((filename, progress))
                    #print("Return code: " + str(retcode) +
                          #" - " + self.exit_codes[retcode])
                    break
        except KeyboardInterrupt:
            proc.send_signal(signal.SIGTERM)
            proc.wait()
            retcode = proc.returncode

        progress_queue.put(("exit", retcode))
        return retcode


def print_progressbar(percentage, file, status=None):
    """ Print a simple progress bar. """
    from os import popen
    _, cols = popen("stty size", "r").read().split()
    half = int(int(cols) / 2)

    # Not very pretty... Sorry :p
    tmp = "\r" + file
    tmp = tmp[:half - 5] + (tmp[half - 5:] and "... ")
    fmt = "[{0:" + str(half - 6) + "s}] {1:<3}%"
    print(tmp.ljust(half - 3) + fmt.format('#' * int((percentage / 100) *
         (half - 6)), percentage).rjust(half), end="")
    if status:
        print("\n(" + status + ")", end="")


def _read_word(stdout):
    """ Read one white-space delimited word from the io interface. """
    buffer = b""
    char = ""
    while not char.isspace():
        char = stdout.read(1)
        buffer += char
        if not char:
            break
    return buffer.decode()


def is_rarfile(path):
    """ Returns True if path is valid RAR file, else False. """
    try:
        with open(path, "rb") as rarfile:
            # Read the 7 byte magic marker
            marker = rarfile.read(7)
            result = bytes.fromhex("526172211a0700")
            return marker == result
    except IOError:
        # Error or file does not exist
        return False

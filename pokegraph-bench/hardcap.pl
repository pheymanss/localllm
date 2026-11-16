#!/usr/bin/perl
# usage: hardcap.pl <seconds> cmd args...   kills the whole process group at the deadline
my $secs = shift; my $pid = fork();
if ($pid == 0) { setpgrp(0, 0); exec @ARGV or exit 127; }
local $SIG{ALRM} = sub { kill 'TERM', -$pid; sleep 5; kill 'KILL', -$pid; };
alarm $secs; waitpid($pid, 0); my $rc = $? >> 8; alarm 0; exit $rc;

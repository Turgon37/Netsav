#! /bin/sh
### BEGIN INIT INFO
# Provides:          netsav
# Required-Start:    $local_fs $remote_fs $syslog
# Required-Stop:     $local_fs $remote_fs $syslog
# Should-Start:      $time $network iptables firehol shorewall ipmasq arno-iptables-firewall postfix mail-transport-agent
# Should-Stop:       $network iptables firehol shorewall ipmasq arno-iptables-firewall
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start/stop netsav
# Description:       Start/stop netsav, a network system availability checker
#                    for remote host
### END INIT INFO

# Author: Pierre GINDRAUD <pgindraud@gmail.com>

PATH=/usr/sbin:/usr/bin:/sbin:/bin
DESC="NETwork System Availability Verifier"
NAME=netsav
DAEMON=/usr/bin/$NAME-launcher
PIDFILE=/var/run/netsav.pid
DAEMON_ARGS=""

SCRIPTNAME=/etc/init.d/$NAME

# Exit if the package is not installed
[ -x "$DAEMON" ] || exit 0

# Read configuration variable file if it is present
[ -r /etc/default/$NAME ] && . /etc/default/$NAME

# Load the VERBOSE setting and other rcS variables
#. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.2-14) to ensure that this file is present
# and status_of_proc is working.
. /lib/lsb/init-functions



#
# Function that starts the daemon/service
#
# Return
#   0 if daemon has been started
#   1 if daemon was already running
#   2 if daemon could not be started
do_start()
{
  do_status && return 1

  DAEMON_ARGS="$DAEMON_ARGS -p $PIDFILE -b"

  start-stop-daemon --start --quiet --pidfile $PIDFILE --exec $DAEMON -- > /dev/null \
    $DAEMON_ARGS \
    || return 2

  return 0
}

#
# Function that return the daemon/service's status
#
# Return
#   0 if daemon is running
#   1 if daemon isn't running
do_status() {
  pidofproc $DAEMON >/dev/null 
  return $?
}

#
# Function that stops the daemon/service
#
# Return
#   0 if daemon has been stopped
#   1 if daemon was already stopped
#   2 if daemon could not be stopped
#   other if a failure occurred
do_stop()
{
  do_status || return 1

  start-stop-daemon --stop --quiet --signal TERM --pidfile $PIDFILE
  while [ -f $PIDFILE ]; do

    sleep 1
  done
  return 0
}



case "$1" in
  start)
    [ "$VERBOSE" != no ] && log_daemon_msg "Starting $DESC" "$NAME"
    do_start
    case "$?" in
      0) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
      1)
        if [ "$VERBOSE" != no ]; then
          log_end_msg 0
          log_success_msg "Deamon already running" "$NAME"
          log_end_msg 0
        fi
      ;;
      2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
    esac
  ;;
  stop)
    [ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC" "$NAME"
    do_stop
    case "$?" in
      0) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
      1)
        if [ "$VERBOSE" != no ]; then
          log_end_msg 0
          log_success_msg "Deamon already stopped" "$NAME"
        fi
      ;;
      2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
    esac
  ;;
  status)
    do_status
    if [ $? -eq 0 ]; then
      log_success_msg "$NAME is running"
      return 0
    else
      log_failure_msg "$NAME is not running"
      return 1
    fi

  ;;
  restart|force-reload)
    log_daemon_msg "Restarting $DESC" "$NAME"
    do_stop
    case "$?" in
    0|1)
      do_status
      while [ $? -eq 0 ]; do
        sleep 1
        do_status
      done
      do_start
      case "$?" in
      0)
        log_end_msg 0
        log_success_msg "Successful restart : $NAME"
        ;;
      1) # Old process is still running
        log_end_msg 1
        log_failure_msg "Old process is still running : $NAME"
        ;;
      *) # Failed to start
        log_end_msg 1
        log_failure_msg "Failed to start : $NAME"
        ;;
      esac
      ;;
    *)
      # Failed to stop
      log_end_msg 1
      log_failure_msg "Failed to stop : $NAME"
      ;;
    esac
  ;;
  *)
    echo "Usage: $SCRIPTNAME {start|stop|status|restart|force-reload}" >&2
    exit 3
  ;;
esac

:

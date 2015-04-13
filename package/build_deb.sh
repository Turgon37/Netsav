#!/bin/bash
#title         :Debian package building
#description   :Configure rules for iptables firewall
#author        :P.GINDRAUD
#author_contact:pgindraud@gmail.com
#created_on    :2015-03-29
#usage         :./build_deb.sh
#==============================================================================
# CHANGE THIS TO THE NAME OF YOUR PROGRAM, THIS NAME WILL BE THE PACKAGE NAME
NAME=netsav



#========== INTERNAL OPTIONS ==========#
DPKG_DEB=$(which dpkg-deb 2>/dev/null)
SUDO=$(which sudo 2>/dev/null)

#========== INTERNAL VARIABLES ==========#
PACKAGE_ROOT=deb/$NAME
PROJECT=..
VERSION=$(grep '--ignore-case' 'version' DEBIAN/control | grep -Eo '[0-9]+(\.[0-9]+)+')


#========== INTERNAL FUNCTIONS ==========#

# Print a msg to stderr if verbose option is set
# @param[string] : the msg to write in stderr
function _error() {
  echo -e "Error : $@" 1>&2
}

# Check if the script is run by root or not. If not, prompt error and exit
function _isRunAsRoot() {
  if [[ $(id -u) == "0" ]]; then
    SUDO=
    return
  fi
  if [[ -z $SUDO ]]; then
    _error "This script must be run as root." 1>&2
    exit 200
  fi
}

function buildTree() {
  echo ' * Building package tree...'
  if [[ ! -d deb ]]; then
    echo '    => Make the deb directory'
    mkdir deb
    echo '    => Create the full classic debian package tree'
    mkdir -p deb/$NAME/DEBIAN/
    #mkdir -p deb/$NAME/etc/default/
    mkdir -p deb/$NAME/etc/init.d/
    #mkdir -p deb/$NAME/usr/sbin
    mkdir -p deb/$NAME/usr/bin
    chmod -R 755 $PACKAGE_ROOT/*
  else
    echo ' # Deb directory already exists'
    exit 0
  fi
}

function copyFile() {
  echo ' * Copying main files...'
  if [[ -d deb ]]; then
    echo '    => Copy package description files'
    cp -R DEBIAN/* deb/$NAME/DEBIAN/
    # mod for script files
    chmod -R 755 $PACKAGE_ROOT/DEBIAN/p*
    # mod for text files
    chmod -R 644 $PACKAGE_ROOT/DEBIAN/c*
  else
    echo ' # Deb directory does not exists'
  fi
}

function chmodToRoot() {
  $SUDO chown -R root:root $PACKAGE_ROOT
  $SUDO chown -R root:root $PACKAGE_ROOT/*
}


#========== MAIN FUNCTION ==========#
# Main
# @param[] : same of the script
# @return[int] : X the exit code of the script
function main() {
  local r
  
  _isRunAsRoot
  
  ### ARGUMENTS PARSING  
  for i in `seq $(($#+1))`; do
    #catch main arguments
    case $1 in
    -*)
      _error "invalid option -- '$1'"
      exit 201
      ;;
    esac

    shift
  done

  # MAIN CHECK
  if [[ -z $VERSION ]]; then
    _error 'Cannot retrieve package version automatically please set it manually'
    exit 100
  fi

  ### MAIN RUNNING
  umask 022
  
  buildTree
  copyFile
  
  
  echo ' * Applying user building rules...'
  # SET HERE THE COMMAND TO RUN BEFORE MAKE THE PACKET
  # SUCH AS cp BINARY FILE AND MAKE SOME CHMOD

  # copy configuration
  cp $PROJECT/config.conf $PACKAGE_ROOT/etc/netsav.conf
  chmod 640 $PACKAGE_ROOT/etc/netsav.conf

  # copy librairies
  cp -R $PROJECT/netsav $PACKAGE_ROOT/usr/share/
  rm $PACKAGE_ROOT/usr/share/netsav-launcher
  find $PACKAGE_ROOT -name '*pycache*' -type d -exec rm -rf  {} \;

  # copy service binary
  cp $PROJECT/netsav/netsav-launcher $PACKAGE_ROOT/usr/bin/
  chmod 755 $PACKAGE_ROOT/usr/bin/netsav-launcher

  # copy init.d service script
  cp $PROJECT/service/$NAME.init.d $PACKAGE_ROOT/etc/init.d/$NAME
  chmod 755 $PACKAGE_ROOT/etc/init.d/$NAME

  echo ' * Chmoding all tree to root:root...'
  chmodToRoot


  # BUILDING package
  echo ' * Building package...'
  if [[ -n $DPKG_DEB ]]; then
    cd deb
    $SUDO $DPKG_DEB --build ${NAME}
    $SUDO mv $NAME.deb ${NAME}_${VERSION}.deb
    $SUDO chmod 644 ${NAME}_${VERSION}.deb
    echo "  ==> The final package is available in ${NAME}_${VERSION}.deb"
  else
    $SUDO tar cfz ${NAME}_${VERSION}.tar.gz $PACKAGE_ROOT
    $SUDO chmod 644 ${NAME}_${VERSION}.tar.gz
    echo "  ==> The package tree is available in ${NAME}_${VERSION}.tar.gz"
  fi
}


###### RUNNING ######
main "$@"

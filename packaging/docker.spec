Name: docker
Version: 1.7.1
Release: 1
Summary: The open-source application container engine

License: ASL 2.0
Source: %{name}-%{version}.tar.gz

URL: https://dockerproject.org
Vendor: Docker
Packager: Docker <support@docker.com>

# docker builds in a checksum of dockerinit into docker,
# # so stripping the binaries breaks docker
%global __os_install_post %{_rpmconfigdir}/brp-compress
%global debug_package %{nil}
%global _origversion 1.7.1

# required packages for build
# most are already in the container (see contrib/builder/rpm/generate.sh)
# only require systemd on those systems
BuildRequires: pkgconfig(systemd)
BuildRequires: golang
BuildRequires: sqlite-devel
BuildRequires: btrfs-progs-devel
BuildRequires: device-mapper
BuildRequires: device-mapper-devel

## Toolchain specific >>
BuildRequires: eglibc
BuildRequires: eglibc-locale
BuildRequires: eglibc-devel
BuildRequires: eglibc-devel-static
BuildRequires: eglibc-devel-utils
#BuildRequires: fake_binutils
#BuildRequires: fake_binutils-devel
BuildRequires: stbgcc483
#BuildRequires: stbgcc483-cross
BuildRequires: cpp483
BuildRequires: gcc483-locale
#BuildRequires: gcc483-info
BuildRequires: gcc483-c++
BuildRequires: libstdc++-devel
Requires: systemd-units
# End Toolchain specific <<

# required packages on install
Requires: /bin/sh
Requires: iptables
Requires: libcgroup
Requires: tar
Requires: xz

# conflicting packages
#Conflicts: docker
#Conflicts: docker-io

%description
Docker is an open source project to pack, ship and run any application as a
lightweight container

Docker containers are both hardware-agnostic and platform-agnostic. This means
they can run anywhere, from your laptop to the largest EC2 compute instance and
everything in between - and they don't require you to use a particular
language, framework or packaging system. That makes them great building blocks
for deploying and scaling web apps, databases, and backend services without
depending on a particular stack or provider.

%prep
%setup 
# workaround: we need the .git of the upstream docker for building
mv .gittmp .git

%build
# In case random segfault
ulimit -c unlimited
export DOCKER_BUILDTAGS='exclude_graphdriver_devicemapper exclude_graphdriver_btrfs'
#export DOCKER_BUILDTAGS='exclude_graphdriver_devicemapper'
#export DOCKER_BUILDTAGS='exclude_graphdriver_btrfs'
AUTO_GOPATH=1 ./hack/make.sh dynbinary
# ./man/md2man-all.sh runs outside the build container (if at all), since we don't have go-md2man here

%check
./bundles/%{_origversion}/dynbinary/docker -v

%install
# install binary
install -d $RPM_BUILD_ROOT/%{_bindir}
install -p -m 755 bundles/%{_origversion}/dynbinary/docker-%{_origversion} $RPM_BUILD_ROOT/%{_bindir}/docker

# install dockerinit
install -d $RPM_BUILD_ROOT/%{_libexecdir}/docker
install -p -m 755 bundles/%{_origversion}/dynbinary/dockerinit-%{_origversion} $RPM_BUILD_ROOT/%{_libexecdir}/docker/dockerinit

# install udev rules
install -d $RPM_BUILD_ROOT/%{_sysconfdir}/udev/rules.d
install -p -m 755 contrib/udev/80-docker.rules $RPM_BUILD_ROOT/%{_sysconfdir}/udev/rules.d/80-docker.rules

# add init scripts
install -d $RPM_BUILD_ROOT/etc/sysconfig
install -d $RPM_BUILD_ROOT/%{_initddir}


install -d $RPM_BUILD_ROOT/%{_unitdir}
install -p -m 644 contrib/init/systemd/docker.service $RPM_BUILD_ROOT/%{_unitdir}/docker.service
install -p -m 644 contrib/init/systemd/docker.socket $RPM_BUILD_ROOT/%{_unitdir}/docker.socket

install -p -m 644 contrib/init/sysvinit-redhat/docker.sysconfig $RPM_BUILD_ROOT/etc/sysconfig/docker
install -p -m 755 contrib/init/sysvinit-redhat/docker $RPM_BUILD_ROOT/%{_initddir}/docker

# add bash completions
install -d $RPM_BUILD_ROOT/usr/share/bash-completion/completions
install -d $RPM_BUILD_ROOT/usr/share/zsh/vendor-completions
install -d $RPM_BUILD_ROOT/usr/share/fish/completions
install -p -m 644 contrib/completion/bash/docker $RPM_BUILD_ROOT/usr/share/bash-completion/completions/docker
install -p -m 644 contrib/completion/zsh/_docker $RPM_BUILD_ROOT/usr/share/zsh/vendor-completions/_docker
install -p -m 644 contrib/completion/fish/docker.fish $RPM_BUILD_ROOT/usr/share/fish/completions/docker.fish

# install manpages
install -d %{buildroot}%{_mandir}/man1
install -p -m 644 man/man1/*.1 $RPM_BUILD_ROOT/%{_mandir}/man1
install -d %{buildroot}%{_mandir}/man5
install -p -m 644 man/man5/*.5 $RPM_BUILD_ROOT/%{_mandir}/man5

# add vimfiles
install -d $RPM_BUILD_ROOT/usr/share/vim/vimfiles/doc
install -d $RPM_BUILD_ROOT/usr/share/vim/vimfiles/ftdetect
install -d $RPM_BUILD_ROOT/usr/share/vim/vimfiles/syntax
install -p -m 644 contrib/syntax/vim/doc/dockerfile.txt $RPM_BUILD_ROOT/usr/share/vim/vimfiles/doc/dockerfile.txt
install -p -m 644 contrib/syntax/vim/ftdetect/dockerfile.vim $RPM_BUILD_ROOT/usr/share/vim/vimfiles/ftdetect/dockerfile.vim
install -p -m 644 contrib/syntax/vim/syntax/dockerfile.vim $RPM_BUILD_ROOT/usr/share/vim/vimfiles/syntax/dockerfile.vim

# add nano
install -d $RPM_BUILD_ROOT/usr/share/nano
install -p -m 644 contrib/syntax/nano/Dockerfile.nanorc $RPM_BUILD_ROOT/usr/share/nano/Dockerfile.nanorc

# list files owned by the package here
%files
/%{_bindir}/docker
/%{_libexecdir}/docker/dockerinit
/%{_sysconfdir}/udev/rules.d/80-docker.rules
/%{_unitdir}/docker.service
/%{_unitdir}/docker.socket
/etc/sysconfig/docker
/%{_initddir}/docker
/usr/share/bash-completion/completions/docker
/usr/share/zsh/vendor-completions/_docker
/usr/share/fish/completions/docker.fish
%doc
/%{_mandir}/man1/*
/%{_mandir}/man5/*
/usr/share/vim/vimfiles/doc/dockerfile.txt
/usr/share/vim/vimfiles/ftdetect/dockerfile.vim
/usr/share/vim/vimfiles/syntax/dockerfile.vim
/usr/share/nano/Dockerfile.nanorc

%post
%systemd_post docker
if ! getent group docker > /dev/null; then
    groupadd --system docker
fi

%preun
%systemd_preun docker

%postun
%systemd_postun_with_restart docker


# If any of the following macros should be set otherwise,
# you can wrap any of them with the following conditions:
# - %%if 0%%{centos} == 7
# - %%if 0%%{?rhel} == 7
# - %%if 0%%{?fedora} == 23
# Or just test for particular distribution:
# - %%if 0%%{centos}
# - %%if 0%%{?rhel}
# - %%if 0%%{?fedora}
#
# Be aware, on centos, both %%rhel and %%centos are set. If you want to test
# rhel specific macros, you can use %%if 0%%{?rhel} && 0%%{?centos} == 0 condition.
# (Don't forget to replace double percentage symbol with single one in order to apply a condition)

# Generate devel rpm
%global with_devel 1
# Build project from bundled dependencies
%global with_bundled 0
# Build with debug info rpm
%global with_debug 0
# Generate bin files
# Do not forget to enable with_debug as well
%global with_build 0
# Run tests in check section
# Check needs github.com/alecthomas/assert
%global with_check 0
# Generate unit-test rpm
%global with_unit_test 1

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%if ! 0%{?gobuild:1}
%define gobuild(o:) go build -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v -x %{?**};
%endif

%global provider        github
%global provider_tld    com
%global project         alecthomas
%global repo            chroma
# https://github.com/alecthomas/chroma
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          03b0c0d6bb7b9f7f8fd58fca6f1c6a2caffb9ca8
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:           golang-%{provider}-%{project}-%{repo}
Version:        0.1.1
Release:        6.20171017git03b0c0d%{?dist}
Summary:        A general purpose syntax highlighter in pure Go
License:        MIT
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 aarch64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}
%if 0%{?with_build}
Provides: chroma%{?_isa} = %{version}-%{release}

%if ! 0%{?with_bundled}
# _tools/css2style/main.go
BuildRequires: golang(github.com/aymerick/douceur/css)
BuildRequires: golang(github.com/aymerick/douceur/parser)
BuildRequires: golang(gopkg.in/alecthomas/kingpin.v3)

# cmd/chroma/main.go
BuildRequires: golang(github.com/mattn/go-colorable)
BuildRequires: golang(github.com/mattn/go-isatty)

# Remaining dependencies not included in main packages
BuildRequires: golang(github.com/danwakefield/fnmatch)
BuildRequires: golang(github.com/dlclark/regexp2)
%endif
%endif # with_build

%description
%{summary}

%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch

%if 0%{?with_check} && ! 0%{?with_bundled}
BuildRequires: golang(github.com/danwakefield/fnmatch)
BuildRequires: golang(github.com/dlclark/regexp2)
%endif

Requires:      golang(github.com/danwakefield/fnmatch)
Requires:      golang(github.com/dlclark/regexp2)

Provides:      golang(%{import_path}) = %{version}-%{release}
Provides:      golang(%{import_path}/formatters) = %{version}-%{release}
Provides:      golang(%{import_path}/formatters/html) = %{version}-%{release}
Provides:      golang(%{import_path}/lexers) = %{version}-%{release}
Provides:      golang(%{import_path}/quick) = %{version}-%{release}
Provides:      golang(%{import_path}/styles) = %{version}-%{release}

%description devel
%{summary}

This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%package unit-test-devel
Summary:         Unit tests for %{name} package
%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%if 0%{?with_check} && ! 0%{?with_bundled}
BuildRequires: golang(github.com/stretchr/testify/assert)
BuildRequires: golang(github.com/stretchr/testify/require)
%endif

Requires:      golang(github.com/stretchr/testify/assert)
Requires:      golang(github.com/stretchr/testify/require)

%description unit-test-devel
%{summary}

This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%setup -q -n %{repo}-%{commit}

%build
%if 0%{?with_build}
mkdir -p src/%{provider}.%{provider_tld}/%{project}
ln -s ../../../ src/%{import_path}

%if ! 0%{?with_bundled}
export GOPATH=$(pwd):%{gopath}
%else
# No dependency directories so far
export GOPATH=$(pwd):%{gopath}
%endif

%gobuild -o bin/css2style %{import_path}/_tools/css2style
%gobuild -o bin/exercise %{import_path}/_tools/exercise
%gobuild -o bin/chroma %{import_path}/cmd/chroma
%endif # with_build

%install
%if 0%{?with_build}
install -d -p %{buildroot}%{_bindir}
install -p -m 0755 bin/css2style %%{buildroot}%%{_bindir}
install -p -m 0755 bin/exercise %%{buildroot}%%{_bindir}
install -p -m 0755 bin/chroma %{buildroot}%{_bindir}
%endif # with_build

# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%dir %%{gopath}/src/%%{import_path}/." >> devel.file-list
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . \( -iname "*.go" -or -iname "*.s" \) \! -iname "*_test.go") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
%endif

# testing files for this project
%if 0%{?with_unit_test} && 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test-devel.file-list
for file in $(find . -iname "*_test.go") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test-devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
%endif

%if 0%{?with_devel}
sort -u -o devel.file-list devel.file-list
%endif

%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%if ! 0%{?with_bundled}
export GOPATH=%{buildroot}/%{gopath}:%{gopath}
%else
# No dependency directories so far

export GOPATH=%{buildroot}/%{gopath}:%{gopath}
%endif

%if ! 0%{?gotest:1}
%global gotest go test
%endif

%gotest %{import_path}
%gotest %{import_path}/formatters/html
%gotest %{import_path}/lexers
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%if 0%{?with_build}
%files
%license COPYING
%doc README.md
%{_bindir}/css2style
%{_bindir}/exercise
%{_bindir}/chroma
%endif # with_build

%if 0%{?with_devel}
%files devel -f devel.file-list
%license COPYING
%doc README.md
%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%files unit-test-devel -f unit-test-devel.file-list
%license COPYING
%doc README.md
%endif

%changelog
* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.1-6.20171017git03b0c0d
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.1-5.20171017git03b0c0d
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Sat Oct 21 2017 Athos Ribeiro <athoscr@fedoraproject.org> - 0.1.1-4.20171017git03b0c0d
- Disabling check until github.com/alecthomas/assert hits rawhide

* Sat Oct 21 2017 Athos Ribeiro <athoscr@fedoraproject.org> - 0.1.1-3.20171017git03b0c0d
- Update to latest revision

* Sat Oct 14 2017 Athos Ribeiro <athoscr@fedoraproject.org> - 0.1.1-2
- Fix build paths for exercise and css2style
- Add BR for gopkg.in/alecthomas/kingpin.v3
- Do not build bin files until kingpin v3 is released

* Wed Oct 11 2017 Athos Ribeiro <athoscr@fedoraproject.org> - 0.1.1-1
- First package for Fedora

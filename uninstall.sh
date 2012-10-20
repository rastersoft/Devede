#!/bin/bash


uninstall_locales()	# arg1=datadir.

{
	rm -f "${DESTDIR}${1}/locale/"*"/LC_MESSAGES/devede.mo"
}


uninstall_others()	# arg1=bindir, arg2=datadir, arg3=pkglibdir,
			#	arg4=pkgdatadir, arg5=pkgdocdir.

{
	rm -f "${DESTDIR}${1}/devede"
	rm -f "${DESTDIR}${1}/devede.py"
	rm -f "${DESTDIR}${1}/devede_debug"
        rm -f "${DESTDIR}${1}/devede-debug"
	rm -rf "${DESTDIR}${3}"
	rm -rf "${DESTDIR}${4}"
	rm -rf "${DESTDIR}${5}"
	rm -f "${DESTDIR}${2}/pixmaps/devede.png"
	rm -f "${DESTDIR}${2}/pixmaps/devede.svg"
	rm -f "${DESTDIR}${2}/applications/devede.desktop"
}


#	Process arguments.

PARAM=

for arg
do	if [ "${PARAM}" ]
	then	eval "${PARAM}=\"${arg}\""
		PARAM=
	else
		case "${arg}" in

		--*)	PARAM="${arg: 2}"
			;;

		-*)	PARAM="${arg: 1}"
			;;

		*)	PARAM="${arg}"
			;;
		esac

		case "${PARAM}" in

		*=*)	eval "${PARAM}"
			PARAM=
			;;
		esac
	fi
done

if [ "${PARAM}" ]
then	eval "${PARAM}="
fi

DESTDIR="${DESTDIR:-}"

#	Version is targeted if specified as such, or if a parameter is set.

targeted=${targeted:-${prefix}${bindir}${libdir}${datadir}${docdir}\
${pkglibdir}${pkgdatadir}${pkgdocdir}${DESTDIR}no}

if [ "${targeted}" = "no" ]
then
	#	Version is not targeted. Uninstall legacy and current versions
	#		in default paths (relative to DESTDIR).

	uninstall_locales "/usr/share"		# Locales are common.

	#	Remove legacy version.

	uninstall_others	"/usr/bin"				\
				"/usr/share"				\
				"/usr/lib/devede"			\
				"/usr/share/devede"			\
				"/usr/share/doc/devede"

	#	Remove current version.

	uninstall_others	"/usr/local/bin"			\
				"/usr/local/share"			\
				"/usr/local/lib/devede"			\
				"/usr/local/share/devede"		\
				"/usr/local/share/doc/devede"
else
	#	Be sure all paths are defined.

	prefix="${prefix:-/usr/local}"
	bindir="${bindir:-${prefix}/bin}"
	libdir="${libdir:-${prefix}/lib}"
	datadir="${datadir:-${prefix}/share}"
	docdir="${docdir:-${datadir}/doc}"
	pkglibdir="${pkglibdir:-${libdir}/devede}"
	pkgdatadir="${pkgdatadir:-${datadir}/devede}"
	pkgdocdir="${pkgdocdir:-${docdir}/devede}"

	#	Remove targeted version.

	uninstall_locales "${datadir}"
	uninstall_others	"${bindir}"				\
				"${datadir}"				\
				"${pkglibdir}"				\
				"${pkgdatadir}"				\
				"${pkgdocdir}"
fi

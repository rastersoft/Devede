#!/bin/bash

#	Get script directory path.

scriptdir="`dirname ${0}`"
DESTDIR="${DESTDIR:-}"


install_lang()		# arg1=datadir, arg2=locale, arg3=<lang file name>.

{
	install -m 755 -d "${DESTDIR}${1}/locale/${2}/LC_MESSAGES"
	install -m 644 "${scriptdir}/po/${3}.mo"			\
		"${DESTDIR}${1}/locale/${2}/LC_MESSAGES/devede.mo"
}


install_locales()	# arg1=datadir.

{
	install_lang "${1}"	ca	ca		# Catala
	install_lang "${1}"	cs	cs_CZ		# Czech
	install_lang "${1}"	da	da		# Danish
	install_lang "${1}"	de_DE	de_DE		# German
	install_lang "${1}"	el	el		# Greek
	install_lang "${1}"	es	es		# Spanish
	install_lang "${1}"	fr	fr		# French
	install_lang "${1}"	gl	gl		# Galego
	install_lang "${1}"	hu_HU	hu_HU		# Hungarian
	install_lang "${1}"	it_IT	it_IT		# Italian
	install_lang "${1}"	nb_NO	nb_NO		# Norwegian
	install_lang "${1}"	nl	nl		# Netherlands
	install_lang "${1}"	pl	pl		# Poland
	install_lang "${1}"	pt_BR	pt_BR		# Brazilian portugues.
	install_lang "${1}"     pt_PT   pt_PT           # Portugues
	install_lang "${1}"	ru	ru		# Russian
	install_lang "${1}"     sk      sk              # Slovak
	install_lang "${1}"	sv	sv		#
	install_lang "${1}"	tr	tr		# Turkish
	install_lang "${1}"	zh_TW	zh_TW		# Taiwanese
	install_lang "${1}"     zh_CN   zh_CN           # Simplified Chinese
}


install_others()	# arg1=bindir, arg2=datadir, arg3=pkglibdir,
			#	arg4=pkgdatadir, arg5=pkgdocdir.

{
	install -m 755 -d "${DESTDIR}${1}"
	install -m 755 "${scriptdir}/devede.py" "${DESTDIR}${1}/devede"
	install -m 755 "${scriptdir}/devede_debug" "${DESTDIR}${1}/devede_debug"
	install -m 755 "${scriptdir}/devede-debug" "${DESTDIR}${1}/devede-debug"

	install -m 755 -d "${DESTDIR}${3}"
	install "${scriptdir}"/devede_*.py "${DESTDIR}${3}/"

	install -m 755 -d "${DESTDIR}${4}"
	install -m 755 -d "${DESTDIR}${4}/backgrounds"
	install -m 644 "${scriptdir}/interface"/* "${DESTDIR}${4}/"
	install -m 644 "${scriptdir}/devedesans.ttf" "${DESTDIR}${4}/"
	install -m 644 "${scriptdir}/pixmaps"/* "${DESTDIR}${4}/" 2>/dev/null
	install -m 644 "${scriptdir}/pixmaps/backgrounds"/* "${DESTDIR}${4}/backgrounds/"
	install -m 644 "${scriptdir}/devede.svg" "${DESTDIR}${4}/"

	install -m 755 -d "${DESTDIR}${2}/pixmaps"
	install -m 644 "${scriptdir}/devede.svg" "${DESTDIR}${2}/pixmaps/"

	install -m 755 -d "${DESTDIR}${2}/pixmaps/backgrounds"
	install -m 644 "${scriptdir}/devede.svg" "${DESTDIR}${2}/pixmaps/"

	install -m 755 -d "${DESTDIR}${2}/applications"
	install -m 644 "${scriptdir}/devede.desktop"			\
						"${DESTDIR}${2}/applications/"

	install -m 755 -d "${DESTDIR}${5}"
	install -m 644 "${scriptdir}/docs"/c* "${DESTDIR}${5}"

	install -m 755 -d "${DESTDIR}${5}/html"
	install -m 644 "${scriptdir}/docs/html"/* "${DESTDIR}${5}/html"

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

#	Uninstall older versions if needed.

[ "${uninstall}" = "no" ] || "${scriptdir}/uninstall.sh" "${@}"

#	Version is targeted if specified as such, or if a parameter is set.

targeted=${targeted:-${prefix}${bindir}${libdir}${datadir}${docdir}\
${pkglibdir}${pkgdatadir}${pkgdocdir}${DESTDIR}no}

if [ "${targeted}" = "no" ]
then
	#	Version is not targeted. Install new version to the default
	#		paths (relative to DESTDIR).

	install_locales "/usr/share"		# Locales are common.

	install_others	"/usr/local/bin"				\
			"/usr/local/share"				\
			"/usr/local/lib/devede"				\
			"/usr/local/share/devede"			\
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

	#	And now, install everything according to paths above.

	install_locales "${datadir}"
	install_others	"${bindir}"					\
			"${datadir}"					\
			"${pkglibdir}"					\
			"${pkgdatadir}"					\
			"${pkgdocdir}"
fi

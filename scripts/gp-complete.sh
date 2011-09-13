# Bash completion support for globus provision
# Completes --options and gpi-* instance names 
# for each tool.

_gp_completer() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
	case $1 in
		gp-instance-create)
			opts="--help --verbose --debug --instances-dir --conf --topology"
			gpi=false
			;;
		gp-instance-describe)
			opts="--help --verbose --debug --instances-dir"
			gpi=true
			;;
		gp-instance-start)
			opts="--help --verbose --debug --instances-dir --extra-files --run"
			gpi=true
			;;
		gp-instance-stop)
			opts="--help --verbose --debug --instances-dir"
			gpi=true
			;;
		gp-instance-update)
			opts="--help --verbose --debug --instances-dir --topology --extra-files --run"
			gpi=true
			;;
		gp-instance-terminate)
			opts="--help --verbose --debug --instances-dir"
			gpi=true
			;;
		gp-instance-list)
			opts="--help --verbose --debug --instances-dir"
			gpi=true
			;;
	esac
	
	if $gpi; then
		instances=`ls ~/.globusprovision/instances/`
	    last_instance_file=/tmp/.globusprovision-$UID/$BASHPID
	    
	    if [ -f $last_instance_file ];
	    then
	    	last_instance=`cat $last_instance_file`
	    else
	    	last_instance="$instances"
	    fi	
	fi

	case $prev in
		"-h"|"--help")
			return 1
			;;
		"-v"|"--verbose"|"-d"|"--debug"|$1)
			if $gpi; then
				if [[ ${cur} == "" ]] ; then
					COMPREPLY=( $(compgen -W "${last_instance}" -- ${cur}) )
				elif [[ ${cur} == -* ]]; then
					COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
				elif [[ ${cur} == gpi-* ]]; then
					COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
				else
					return 1
				fi
			else
				COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
			fi
			;;
		"-i"|"--instances-dir"|"-c"|"--conf"|"-t"|"--topology")
			if [[ ${cur} == -* ]] ; then
				COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
			else
				case $prev in
					"-i"|"--instances-dir")
						COMPREPLY=( $(compgen -A directory -- ${cur}) )
						;;
					"-c"|"--conf")
						COMPREPLY=( $(compgen -o dirnames -f -X '!*.conf' -- ${cur}) )
						;;
					"-t"|"--topology")
						COMPREPLY=( $(compgen -o dirnames -f -X '!*.@(conf|json)' -- ${cur}) )
						;;
					"-x"|"--extra-files")
						COMPREPLY=( $(compgen -f -- ${cur}) )
						;;
					"-r"|"--run")
						COMPREPLY=( $(compgen -f -- ${cur}) )
						;;
				esac
			fi
			;;
		*)
			
			;;		
	esac	
	
	return 0
}
complete -o default -F _gp_completer gp-instance-create
complete -o default -F _gp_completer gp-instance-start
complete -o default -F _gp_completer gp-instance-stop
complete -o default -F _gp_completer gp-instance-describe
complete -o default -F _gp_completer gp-instance-terminate
complete -o default -F _gp_completer gp-instance-update
complete -o default -F _gp_completer gp-instance-list


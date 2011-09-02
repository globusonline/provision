# Bash completion support for globus provision
# Completes --options and gpi-* instance names 
# for each tool.


# gp-add-host 
# gp-ec2-update-ami
# gp-start      
_gp_start_completer() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help --verbose --debug --instances-dir --extra-files --run"
	instances=`ls ~/.globusprovision/instances/`

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
	if [[ ${cur} == "" ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
	if [[ ${cur} == gpi-* ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
}
complete -o default -F _gp_start_completer gp-start

# gp-add-user 
# gp-go-register-endpoint 
# gp-stop       
_gp_stop_completer() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help --verbose --debug --instances-dir"
	instances=`ls ~/.globusprovision/instances/`

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
	if [[ ${cur} == "" ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
	if [[ ${cur} == gpi-* ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
}
complete -o default -F _gp_stop_completer gp-stop

# gp-create 
_gp_create_completer() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help --verbose --debug --instances-dir --conf --topology"

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}
complete -o default -F _gp_create_completer gp-create

# gp-list-instances 
# gp-terminate  
_gp_terminate_completer() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help --verbose --debug --instances-dir"
	instances=`ls ~/.globusprovision/instances/`

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
	if [[ ${cur} == "" ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
	if [[ ${cur} == gpi-* ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
}
complete -o default -F _gp_terminate_completer gp-terminate

# gp-describe-instance 
_gp_describe_instance_completer() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help --verbose --debug --instances-dir"
	instances=`ls ~/.globusprovision/instances/`

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
	if [[ ${cur} == "" ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
	if [[ ${cur} == gpi-* ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
}
complete -o default -F _gp_describe_instance_completer gp-describe-instance

# gp-remove-hosts 
# gp-update-topology 
_gp_update_topology_completer() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="--help --verbose --debug --instances-dir --topology --extra-files --run"
	instances=`ls ~/.globusprovision/instances/`

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
	if [[ ${cur} == "" ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
	if [[ ${cur} == gpi-* ]] ; then
        COMPREPLY=( $(compgen -W "${instances}" -- ${cur}) )
		return 0
	fi
}
complete -o default -F _gp_update_topology_completer gp-update-topology

# gp-ec2-create-ami 
# gp-remove-users          

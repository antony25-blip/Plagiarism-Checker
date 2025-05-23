export PATH="/opt/homebrew/bin:$PATH"source 

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/Users/antonysmechery/miniforge3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/Users/antonysmechery/miniforge3/etc/profile.d/conda.sh" ]; then
        . "/Users/antonysmechery/miniforge3/etc/profile.d/conda.sh"
    else
        export PATH="/Users/antonysmechery/miniforge3/bin:$PATH"
    fi
fi
unset __conda_setup

if [ -f "/Users/antonysmechery/miniforge3/etc/profile.d/mamba.sh" ]; then
    . "/Users/antonysmechery/miniforge3/etc/profile.d/mamba.sh"
fi
# <<< conda initialize <<<

